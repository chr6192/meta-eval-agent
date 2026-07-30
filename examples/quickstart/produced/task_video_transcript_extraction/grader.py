"""Video transcript extraction task grader."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from judge_harness import invoke_agentic_judge

_SKIP_DIRS = {"browser", "__pycache__", ".git", "node_modules"}
_TIMESTAMP_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
def _section_header_pattern(section_name: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?im)^#{{1,3}}\s*(?:[^\n]*?\s+)?{re.escape(section_name)}\s*(?:\([^)]*\))?\s*$"
    )
_METADATA_LABELS = {
    "title": re.compile(r"(?i)\b(?:\*\*)?title(?:\*\*)?\b"),
    "channel": re.compile(r"(?i)\b(?:\*\*)?channel(?:\*\*)?\b"),
    "duration": re.compile(r"(?i)\b(?:\*\*)?duration(?:\*\*)?\b"),
    "upload": re.compile(
        r"(?i)\b(?:\*\*)?(?:upload\s*date|uploaded|upload)(?:\*\*)?\b"
    ),
}


def _iter_files(workspace_path: str) -> list[Path]:
    root = Path(workspace_path)
    if not root.is_dir():
        return []
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            out.append(Path(dirpath) / name)
    return out


def _find_named_file(workspace_path: str, basename: str) -> Path | None:
    root = Path(workspace_path) / basename
    if root.is_file():
        return root
    matches = [
        p
        for p in _iter_files(workspace_path)
        if p.name == basename and p.is_file()
    ]
    if not matches:
        return None
    matches.sort(key=lambda p: (len(p.parts), str(p)))
    return matches[0]


def _read_text(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_section(text: str, section_name: str) -> str:
    match = _section_header_pattern(section_name).search(text)
    if not match:
        return ""
    start = match.end()
    rest = text[start:]
    nxt = re.search(r"(?im)^#{1,3}\s+\S", rest)
    return rest[: nxt.start()] if nxt else rest


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text))


_STOPWORDS = {
    "that", "this", "with", "from", "have", "been", "your", "what", "when",
    "they", "them", "will", "would", "about", "into", "than", "then", "also",
    "just", "only", "very", "more", "some", "other", "there", "their", "which",
    "while", "where", "those", "these", "could", "should", "never", "gonna",
}


def _content_words(text: str) -> set[str]:
    words = {
        w.lower()
        for w in re.findall(r"[a-zA-Z']{4,}", text)
        if w.lower() not in _STOPWORDS
    }
    return words


def _transcript_lyric_body(transcript_text: str) -> str:
    lines: list[str] = []
    for raw in transcript_text.splitlines():
        line = raw.strip().lstrip("\ufeff")
        if not line or line.startswith("="):
            continue
        if re.search(r"(?i)transcript|source:|video url|channel:|duration:", line):
            if _word_count(line) < 6:
                continue
        line = re.sub(r"^\[[^\]]+\]\s*", "", line)
        line = re.sub(r"^[♪\s]+|[♪\s]+$", "", line).strip()
        if len(line) >= 8:
            lines.append(line)
    return "\n".join(lines)
def _lyric_lines(transcript_text: str) -> list[str]:
    lines: list[str] = []
    for raw in _transcript_lyric_body(transcript_text).splitlines():
        line = raw.strip().lower()
        if _word_count(line) < 3:
            continue
        lines.append(line)
    uniq: list[str] = []
    seen: set[str] = set()
    for line in sorted(lines, key=len, reverse=True):
        if line not in seen:
            seen.add(line)
            uniq.append(line)
    return uniq


def check_transcript_exists(workspace_path: str) -> float:
    """
    1.0 - transcript.txt present and readable
    0.0 - missing
  反例: 未创建 transcript.txt
    """
    path = _find_named_file(workspace_path, "transcript.txt")
    text = _read_text(path).strip()
    return 1.0 if path and len(text) > 0 else 0.0


def check_transcript_substantive(workspace_path: str) -> float:
    """
    1.0 - >=400 chars, >=5 timestamps, >=8 lyric lines
    0.5 - partial transcript (>=200 chars, >=3 timestamps)
    0.0 - placeholder or empty
  反例: 仅写一行 "transcript unavailable"
    """
    text = _read_text(_find_named_file(workspace_path, "transcript.txt"))
    if not text.strip():
        return 0.0
    stamps = len(_TIMESTAMP_RE.findall(text))
    lyrics = len(_lyric_lines(text))
    size = len(text)
    if size >= 400 and stamps >= 5 and lyrics >= 8:
        return 1.0
    if size >= 200 and stamps >= 3 and lyrics >= 3:
        return 0.5
    return 0.0


def check_summary_exists(workspace_path: str) -> float:
    """
    1.0 - video_summary.md present and non-empty
    0.0 - missing
  反例: 只有 transcript 没有 summary
    """
    path = _find_named_file(workspace_path, "video_summary.md")
    text = _read_text(path).strip()
    return 1.0 if path and len(text) > 50 else 0.0


def check_metadata_fields(workspace_path: str) -> float:
    """
    1.0 - summary lists title, channel, duration, upload date with values
    0.5 - 3 of 4 fields present with values
    0.0 - fewer than 3 fields
  反例: metadata section empty or only has title
    """
    summary = _read_text(_find_named_file(workspace_path, "video_summary.md"))
    if not summary.strip():
        return 0.0
    meta_block = _extract_section(summary, "metadata") or summary[:2500]
    hits = 0
    for label_re in _METADATA_LABELS.values():
        if not label_re.search(meta_block):
            continue
        for line in meta_block.splitlines():
            if not label_re.search(line):
                continue
            value = re.sub(r"(?i)^\|?\s*\*?\*?[^|*]+\*?\*?\s*\|?\s*", "", line)
            value = value.strip("| ").strip()
            if len(value) >= 2 and not label_re.fullmatch(value):
                hits += 1
                break
    if hits >= 4:
        return 1.0
    if hits == 3:
        return 0.5
    return 0.0


def check_summary_word_count(workspace_path: str) -> float:
    """
    1.0 - summary body 200-300 words (inclusive)
    0.5 - 150-199 or 301-350 words
    0.0 - outside those ranges or no summary section
  反例: 50-word stub summary
    """
    summary = _read_text(_find_named_file(workspace_path, "video_summary.md"))
    body = _extract_section(summary, "summary")
    if not body.strip():
        return 0.0
    words = _word_count(body)
    if 200 <= words <= 300:
        return 1.0
    if 150 <= words < 200 or 300 < words <= 350:
        return 0.5
    return 0.0


def check_key_points_bullets(workspace_path: str) -> float:
    """
    1.0 - >=3 bullet takeaways in key points section
    0.5 - 1-2 bullets
    0.0 - none
  反例: key points section missing
    """
    summary = _read_text(_find_named_file(workspace_path, "video_summary.md"))
    section = _extract_section(summary, "key points") or summary
    bullets = re.findall(r"(?m)^\s*[-*]\s+\S", section)
    if len(bullets) >= 3:
        return 1.0
    if len(bullets) >= 1:
        return 0.5
    return 0.0


def check_timestamps_section(workspace_path: str) -> float:
    """
    1.0 - >=3 timestamped notable moments in timestamps section
    0.5 - 1-2 timestamps
    0.0 - none
  反例: summary lacks any timestamped moments
    """
    summary = _read_text(_find_named_file(workspace_path, "video_summary.md"))
    section = (
        _extract_section(summary, "timestamps")
        or _extract_section(summary, "notable timestamps")
        or summary
    )
    stamps = _TIMESTAMP_RE.findall(section)
    if len(stamps) >= 3:
        return 1.0
    if len(stamps) >= 1:
        return 0.5
    return 0.0


def check_transcript_summary_alignment(workspace_path: str) -> float:
    """
    1.0 - >=10 shared content words between transcript lyrics and summary
    0.5 - 5-9 shared words
    0.0 - unrelated summary vs transcript vocabulary
  反例: generic essay with no transcript overlap
    """
    transcript = _read_text(_find_named_file(workspace_path, "transcript.txt"))
    summary = _read_text(_find_named_file(workspace_path, "video_summary.md"))
    if not transcript.strip() or not summary.strip():
        return 0.0
    lyric_text = _transcript_lyric_body(transcript)
    transcript_words = _content_words(lyric_text)
    summary_words = _content_words(summary)
    if not transcript_words:
        return 0.0
    overlap = len(transcript_words & summary_words)
    ratio = overlap / max(1, len(transcript_words))
    if overlap >= 10 and ratio >= 0.2:
        return 1.0
    if overlap >= 5:
        return 0.5
    return 0.0


JUDGE_PROMPT = (
    "You are grading a YouTube video transcript extraction task. "
    "Read transcript.txt and video_summary.md in the workspace. "
    "The summary should be a 200-300 word structured overview grounded in the transcript. "
    "Score each dimension 0.0-1.0 with quoted evidence; give 0 and note no_evidence if missing."
)

JUDGE_SCHEMA = {
    "dimensions": {
        "summary_content_quality": {
            "description": (
                "Is the summary section a coherent 200-300 word overview of the video "
                "content (not keyword stuffing or unrelated filler)?"
            )
        },
        "summary_grounded_in_transcript": {
            "description": (
                "Are the summary's main claims supported by lines or themes present in "
                "transcript.txt rather than obvious hallucinations?"
            )
        },
    }
}


def _load_transcript(transcript: list | str | None) -> list:
    if transcript is None:
        return []
    if isinstance(transcript, str):
        path = Path(transcript)
        if path.is_file():
            rows = []
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
            return rows
        return []
    return transcript


def grade(transcript: list, workspace_path: str) -> dict:
    deterministic_signals = {
        "transcript_file_exists": check_transcript_exists(workspace_path),
        "transcript_substantive": check_transcript_substantive(workspace_path),
        "summary_file_exists": check_summary_exists(workspace_path),
        "metadata_four_fields": check_metadata_fields(workspace_path),
        "summary_word_count_200_300": check_summary_word_count(workspace_path),
        "key_points_bullets": check_key_points_bullets(workspace_path),
        "timestamps_notable_moments": check_timestamps_section(workspace_path),
        "transcript_summary_alignment": check_transcript_summary_alignment(
            workspace_path
        ),
    }

    must_have_keys = [
        "transcript_file_exists",
        "transcript_substantive",
        "summary_file_exists",
        "metadata_four_fields",
        "summary_word_count_200_300",
        "key_points_bullets",
        "timestamps_notable_moments",
        "transcript_summary_alignment",
    ]
    nice_deterministic_keys: list[str] = []

    deterministic_pass = all(
        deterministic_signals[k] >= 0.99 for k in must_have_keys
    )

    transcript_data = _load_transcript(transcript)
    judge_kwargs: dict[str, Any] = {"workspace_path": workspace_path}
    if transcript_data:
        judge_kwargs["transcript"] = transcript_data

    if deterministic_pass:
        judge = invoke_agentic_judge(JUDGE_PROMPT, JUDGE_SCHEMA, **judge_kwargs)
    else:
        judge = invoke_agentic_judge(
            JUDGE_PROMPT, JUDGE_SCHEMA, k=1, **judge_kwargs
        )

    nice_signals = {
        k: deterministic_signals[k] for k in nice_deterministic_keys
    }
    if judge.get("available"):
        nice_signals.update(
            {
                f"agentic_judge_{k}": v["score"]
                for k, v in judge["dimensions"].items()
            }
        )
    else:
        for dim in JUDGE_SCHEMA["dimensions"]:
            nice_signals[f"agentic_judge_{dim}"] = 0.0

    nice_total = (
        sum(nice_signals.values()) / max(1, len(nice_signals))
        if nice_signals
        else 0.0
    )

    outcome_passed = deterministic_pass
    signals = {**deterministic_signals, **nice_signals}
    criteria_list = [
        {"name": k, "must_have": k in must_have_keys} for k in signals
    ]

    return {
        "outcome_passed": outcome_passed,
        "score": nice_total,
        "breakdown": signals,
        "criteria": criteria_list,
        "judge_meta": judge,
        "notes": (
            f"deterministic_pass={deterministic_pass} "
            f"judge_available={judge.get('available', False)}"
        ),
    }
