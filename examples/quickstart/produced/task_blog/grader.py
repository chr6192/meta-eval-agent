"""Grader for blog-post writing task (remote work benefits for software developers)."""
from __future__ import annotations

import re
from pathlib import Path

from judge_harness import invoke_agentic_judge

# Filename comes from the task prompt ("Save it to blog_post.md"), not from candidates.
_DELIVERABLE_BASENAME = "blog_post.md"
_WORD_TARGET = 500
_WORD_TOLERANCE = 50  # ±10% of 500

_JUDGE_PROMPT = (
    "Read the candidate deliverable markdown file at the workspace root (blog_post.md). "
    "Score each dimension 0.0–1.0 with quoted evidence from specific paragraphs. "
    "If the file is missing or empty, score 0 for all dimensions with evidence 'no_evidence'."
)

_JUDGE_SCHEMA = {
    "dimensions": {
        "topic_benefits_remote_work_developers": {
            "description": (
                "Does the post substantively discuss multiple benefits of remote work "
                "specifically for software developers (not generic office workers), "
                "with real arguments rather than keyword stuffing?"
            ),
        },
        "narrative_coherence": {
            "description": (
                "Does the text read as a coherent blog post with logical flow, "
                "connected paragraphs, and no major contradictions?"
            ),
        },
    }
}


def _deliverable_path(workspace_path: str) -> Path:
    return Path(workspace_path) / _DELIVERABLE_BASENAME


def _read_deliverable_text(workspace_path: str) -> str | None:
    path = _deliverable_path(workspace_path)
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _count_words(text: str) -> int:
    """Count alphanumeric tokens (English blog word count).

    1.0 context: ~500 words in a prose blog post.
    0.5 context: very short stub or list without prose.
    0.0 context: empty string.
    """
    return len(re.findall(r"[A-Za-z0-9']+", text))


def check_deliverable_exists(workspace_path: str) -> float:
    """P1: workspace root contains the specified deliverable file.

    1.0 - blog_post.md exists as a regular file at workspace root.
    0.0 - missing or only present in a subdirectory.

    Anti-example: agent saves only output/blog_post.md without root copy → 0.0.
    """
    path = _deliverable_path(workspace_path)
    return 1.0 if path.is_file() else 0.0


def check_deliverable_substantial(workspace_path: str) -> float:
    """P2: deliverable is non-trivial prose, not an empty stub.

    1.0 - stripped text length > 50 characters.
    0.5 - file exists but only 1–50 characters (placeholder).
    0.0 - missing or empty.

    Anti-example: file contains only '# Title' with no body → 0.5 or 0.0.
    """
    text = _read_deliverable_text(workspace_path)
    if text is None:
        return 0.0
    stripped = text.strip()
    if len(stripped) > 50:
        return 1.0
    if len(stripped) > 0:
        return 0.5
    return 0.0


def check_word_count_near_target(workspace_path: str) -> float:
    """P3: word count is approximately 500 as requested.

    Structural check: token count via regex on deliverable text.
    1.0 - 450–550 words (±10% of 500).
    0.5 - 400–449 or 551–600 words (clearly attempted but off spec).
    0.0 - fewer than 400 or more than 600 words, or missing file.

    Anti-example: 300-word stub or 800-word essay → below 0.99 must-have threshold.
    """
    text = _read_deliverable_text(workspace_path)
    if text is None:
        return 0.0
    count = _count_words(text)
    low = _WORD_TARGET - _WORD_TOLERANCE
    high = _WORD_TARGET + _WORD_TOLERANCE
    if low <= count <= high:
        return 1.0
    if 400 <= count < low or high < count <= 600:
        return 0.5
    return 0.0


def check_topic_anchors_present(workspace_path: str) -> float:
    """P4a (nice): minimal topical anchors for remote-work benefits for developers.

    Keyword presence only — capped per meta-rule 09; not a must-have gate signal.
    1.0 - mentions remote-work concept, software-developer audience, and benefit framing.
    0.5 - two of three anchor groups present.
    0.0 - fewer than two groups or missing file.

    Anti-example: essay about office perks with no remote-work mention → 0.0.
    """
    text = _read_deliverable_text(workspace_path)
    if text is None:
        return 0.0
    lower = text.lower()
    remote_hits = any(
        phrase in lower
        for phrase in (
            "remote work",
            "work from home",
            "work-from-home",
            "telecommut",
            "distributed team",
            "wfh",
        )
    )
    dev_hits = any(
        phrase in lower
        for phrase in (
            "software developer",
            "software engineers",
            "software engineer",
            "developers who",
            "developer ",
            "developers ",
            "coding ",
            "programmer",
        )
    )
    benefit_hits = any(
        phrase in lower
        for phrase in (
            "benefit",
            "advantage",
            "improve",
            "better ",
            "gain ",
            "boost",
            "helps ",
            "empower",
        )
    )
    groups = sum([remote_hits, dev_hits, benefit_hits])
    if groups >= 3:
        return 1.0
    if groups == 2:
        return 0.5
    return 0.0


def grade(transcript: list, workspace_path: str) -> dict:
    deterministic_signals = {
        "deliverable_exists": check_deliverable_exists(workspace_path),
        "deliverable_substantial": check_deliverable_substantial(workspace_path),
        "word_count_near_500": check_word_count_near_target(workspace_path),
        "topic_anchors_present": check_topic_anchors_present(workspace_path),
    }

    must_have_keys = [
        "deliverable_exists",
        "deliverable_substantial",
        "word_count_near_500",
    ]
    nice_deterministic_keys = ["topic_anchors_present"]

    deterministic_pass = all(
        deterministic_signals[k] >= 0.99 for k in must_have_keys
    )

    if deterministic_pass:
        judge = invoke_agentic_judge(
            _JUDGE_PROMPT,
            _JUDGE_SCHEMA,
            workspace_path=workspace_path,
            transcript=transcript,
        )
    else:
        judge = invoke_agentic_judge(
            _JUDGE_PROMPT,
            _JUDGE_SCHEMA,
            workspace_path=workspace_path,
            transcript=transcript,
            k=1,
        )

    nice_signals: dict[str, float] = {
        k: deterministic_signals[k] for k in nice_deterministic_keys
    }
    # Include word-count partial credit in score for spread among FAIL candidates (rule 16).
    nice_signals["word_count_near_500"] = deterministic_signals["word_count_near_500"]
    if judge.get("available"):
        for dim, payload in judge.get("dimensions", {}).items():
            if isinstance(payload, dict) and isinstance(payload.get("score"), (int, float)):
                nice_signals[f"agentic_judge_{dim}"] = float(payload["score"])
    else:
        for dim in _JUDGE_SCHEMA["dimensions"]:
            nice_signals[f"agentic_judge_{dim}"] = 0.0

    nice_total = (
        sum(nice_signals.values()) / max(1, len(nice_signals))
        if nice_signals
        else 0.0
    )

    signals = {**deterministic_signals, **nice_signals}
    criteria_list = [
        {"name": k, "must_have": k in must_have_keys} for k in signals
    ]

    return {
        "outcome_passed": deterministic_pass,
        "score": nice_total,
        "breakdown": signals,
        "criteria": criteria_list,
        "judge_meta": judge,
        "notes": (
            f"deterministic_pass={deterministic_pass} "
            f"judge_available={judge.get('available', False)}"
        ),
    }
