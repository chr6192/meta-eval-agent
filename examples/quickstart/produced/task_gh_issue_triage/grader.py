"""GitHub issue triage task grader.

Deterministic truth is fetched live from the gh CLI against the task repository.
Deliverable structure is checked against that API-derived fixture.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from judge_harness import invoke_agentic_judge

REPORT_BASENAME = "triage_report.md"
REPO_SLUG = "testuser/my-project"

PRIORITY_RANK = {
    "critical": 0,
    "p0": 0,
    "urgent": 0,
    "blocker": 0,
    "high": 1,
    "p1": 1,
    "medium": 2,
    "p2": 2,
    "moderate": 2,
    "low": 3,
    "p3": 3,
    "minor": 4,
    "p4": 4,
    "backlog": 5,
    "info": 6,
    "documentation": 6,
}

JUDGE_PROMPT = (
    "You are grading a GitHub issue triage task for repository "
    f"{REPO_SLUG}. Read triage_report.md and any issue-comment files in the "
    "workspace. The agent should have posted analysis on the most critical open "
    "issue. Score each dimension 0.0-1.0 with quoted evidence; use 0 and "
    "no_evidence when proof is missing."
)

JUDGE_SCHEMA = {
    "dimensions": {
        "critical_comment_substantive": {
            "description": (
                "The comment on the highest-priority issue gives concrete analysis "
                "and actionable next steps tied to that issue, not generic filler."
            )
        },
        "triage_reasoning_coherent": {
            "description": (
                "triage_report.md assigns priorities and recommended actions that "
                "logically follow from each item's described impact, without "
                "contradictions."
            )
        },
    }
}


def grade(transcript: list, workspace_path: str) -> dict:
    ws = Path(workspace_path)
    report_path = _find_report(ws)
    report_text = report_path.read_text(encoding="utf-8", errors="replace") if report_path else ""

    fixture = _fetch_repo_fixture()
    issues = fixture.get("issues", [])
    prs = fixture.get("pull_requests", [])
    gh_available = fixture.get("available", False)

    deterministic_signals: dict[str, float] = {}
    deterministic_signals["report_file_exists"] = _score_report_exists(report_path, report_text)
    deterministic_signals["all_items_covered"] = _score_items_covered(
        report_text, issues, prs, gh_available
    )
    deterministic_signals["required_fields_per_item"] = _score_required_fields(
        report_text, issues, prs, gh_available
    )
    deterministic_signals["priority_sorted"] = _score_priority_sorted(
        report_text, issues, prs, gh_available
    )
    deterministic_signals["critical_issue_comment_posted"] = _score_critical_comment(
        report_text, issues, gh_available
    )

    must_have_keys = [
        "report_file_exists",
        "all_items_covered",
        "required_fields_per_item",
        "priority_sorted",
        "critical_issue_comment_posted",
    ]
    deterministic_pass = all(deterministic_signals[k] >= 0.99 for k in must_have_keys)

    if deterministic_pass:
        judge = invoke_agentic_judge(
            JUDGE_PROMPT, JUDGE_SCHEMA, workspace_path=workspace_path, transcript=transcript
        )
    else:
        judge = invoke_agentic_judge(
            JUDGE_PROMPT,
            JUDGE_SCHEMA,
            workspace_path=workspace_path,
            transcript=transcript,
            k=1,
        )

    nice_signals: dict[str, float] = {}
    if judge.get("available"):
        nice_signals.update(
            {f"agentic_judge_{k}": v["score"] for k, v in judge.get("dimensions", {}).items()}
        )
    nice_total = sum(nice_signals.values()) / max(1, len(nice_signals)) if nice_signals else 0.0

    signals = {**deterministic_signals, **nice_signals}
    criteria_list = [{"name": k, "must_have": k in must_have_keys} for k in signals]
    return {
        "outcome_passed": deterministic_pass,
        "score": nice_total,
        "breakdown": signals,
        "criteria": criteria_list,
        "judge_meta": judge,
        "notes": (
            f"deterministic_pass={deterministic_pass} gh_available={gh_available} "
            f"judge_available={judge.get('available', False)}"
        ),
    }


def _find_report(workspace: Path) -> Path | None:
    for candidate in (
        workspace / REPORT_BASENAME,
        workspace / "output" / REPORT_BASENAME,
    ):
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    for path in workspace.rglob(REPORT_BASENAME):
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def _score_report_exists(report_path: Path | None, report_text: str) -> float:
    """
    1.0 - triage_report.md exists and has substantive content (>100 chars)
    0.0 - missing or empty
    反例: 空文件或只有标题一行
    """
    if report_path is None:
        return 0.0
    return 1.0 if len(report_text.strip()) > 100 else 0.0


def _fetch_repo_fixture() -> dict[str, Any]:
    """Pull open issues/PRs from gh API (fixture truth, not hardcoded titles)."""
    issues = _gh_json(
        [
            "issue",
            "list",
            "--repo",
            REPO_SLUG,
            "--state",
            "open",
            "--json",
            "number,title,labels,comments",
        ]
    )
    prs = _gh_json(
        [
            "pr",
            "list",
            "--repo",
            REPO_SLUG,
            "--state",
            "open",
            "--json",
            "number,title,labels",
        ]
    )
    if issues is None and prs is None:
        return {"available": False, "issues": [], "pull_requests": []}
    return {
        "available": True,
        "issues": issues or [],
        "pull_requests": prs or [],
    }


def _gh_json(args: list[str]) -> list[dict[str, Any]] | None:
    env = os.environ.copy()
    try:
        proc = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, list) else None


def _score_items_covered(
    report_text: str,
    issues: list[dict[str, Any]],
    prs: list[dict[str, Any]],
    gh_available: bool,
) -> float:
    """
    1.0 - every gh open issue and PR number+title tokens appear in the report
    0.5 - at least half covered
    0.0 - fewer than half or gh unavailable
    反例: 报告只写虚构的 #101 而遗漏真实 #1/#2/#3
    """
    if not gh_available or not report_text.strip():
        return 0.0
    items = [("issue", i) for i in issues] + [("pr", p) for p in prs]
    if not items:
        return 0.0
    hits = sum(1 for kind, item in items if _item_referenced(report_text, kind, item))
    ratio = hits / len(items)
    if ratio >= 1.0:
        return 1.0
    if ratio >= 0.5:
        return 0.5
    return 0.0


def _item_referenced(report_text: str, kind: str, item: dict[str, Any]) -> bool:
    number = item.get("number")
    title = str(item.get("title", "")).strip()
    if number is None:
        return False
    number_patterns = [
        rf"(?i)#\s*{number}\b",
        rf"(?i)\b(?:issue|pr|pull\s+request)\s*#?\s*{number}\b",
        rf"(?i)\|\s*{number}\s*\|",
    ]
    if not any(re.search(p, report_text) for p in number_patterns):
        return False
    title_tokens = _title_tokens(title)
    if not title_tokens:
        return True
    matched_tokens = sum(1 for tok in title_tokens if tok.lower() in report_text.lower())
    return matched_tokens >= max(1, len(title_tokens) // 2)


def _title_tokens(title: str) -> list[str]:
    stop = {"a", "an", "the", "to", "for", "in", "on", "and", "or", "of", "with", "add", "fix"}
    tokens = [t for t in re.findall(r"[A-Za-z0-9]{3,}", title) if t.lower() not in stop]
    return tokens[:4]


def _score_required_fields(
    report_text: str,
    issues: list[dict[str, Any]],
    prs: list[dict[str, Any]],
    gh_available: bool,
) -> float:
    """
    1.0 - each referenced item has priority, category, and recommended action nearby
    0.5 - majority of items have all three fields
    0.0 - otherwise
    反例: 只列标题无 priority/category/action
    """
    if not gh_available or not report_text.strip():
        return 0.0
    items = [("issue", i) for i in issues] + [("pr", p) for p in prs]
    if not items:
        return 0.0
    complete = 0
    referenced = 0
    for kind, item in items:
        if not _item_referenced(report_text, kind, item):
            continue
        referenced += 1
        window = _item_window(report_text, item.get("number"))
        if _window_has_fields(window):
            complete += 1
    if referenced == 0:
        return 0.0
    ratio = complete / referenced
    if ratio >= 1.0:
        return 1.0
    if ratio >= 0.5:
        return 0.5
    return 0.0


def _item_window(report_text: str, number: Any) -> str:
    if number is None:
        return report_text
    pattern = rf"(?is)(.{{0,1200}}#\s*{number}\b.{{0,1200}})"
    match = re.search(pattern, report_text)
    return match.group(1) if match else report_text


def _window_has_fields(window: str) -> bool:
    lower = window.lower()
    has_priority = bool(re.search(r"(?i)\b(priority|p[0-4]|critical|high|medium|low|urgent)\b", window))
    has_category = bool(
        re.search(
            r"(?i)\b(category|type|labels?|security|bug|feature|enhancement|documentation)\b",
            window,
        )
    )
    has_action = bool(
        re.search(
            r"(?i)\b(recommended\s+action|recommend|action|next\s+step|should|merge|fix|address|triage)\b",
            lower,
        )
    )
    return has_priority and has_category and has_action


def _score_priority_sorted(
    report_text: str,
    issues: list[dict[str, Any]],
    prs: list[dict[str, Any]],
    gh_available: bool,
) -> float:
    """
    1.0 - items appear in non-decreasing priority rank order (higher priority first)
    0.5 - one inversion or ambiguous ordering
    0.0 - multiple inversions or cannot parse
    反例: low-priority dark mode 排在 critical login bug 之前
    """
    if not gh_available or not report_text.strip():
        return 0.0
    items = [("issue", i) for i in issues] + [("pr", p) for p in prs]
    ranks: list[int] = []
    positions: list[int] = []
    for kind, item in items:
        number = item.get("number")
        if number is None:
            continue
        pos = _first_position(report_text, number)
        if pos < 0:
            continue
        window = _item_window(report_text, number)
        rank = _extract_priority_rank(window)
        if rank is None:
            continue
        ranks.append(rank)
        positions.append(pos)
    if len(ranks) < 2:
        return 0.5 if ranks else 0.0
    ordered_pairs = sorted(zip(positions, ranks), key=lambda x: x[0])
    ordered_ranks = [r for _, r in ordered_pairs]
    inversions = sum(
        1 for i in range(len(ordered_ranks) - 1) if ordered_ranks[i] > ordered_ranks[i + 1]
    )
    if inversions == 0:
        return 1.0
    if inversions == 1:
        return 0.5
    return 0.0


def _first_position(text: str, number: Any) -> int:
    match = re.search(rf"(?i)#\s*{number}\b", text)
    return match.start() if match else -1


def _extract_priority_rank(window: str) -> int | None:
    lower = window.lower()
    found: list[int] = []
    for key, rank in PRIORITY_RANK.items():
        if re.search(rf"\b{re.escape(key)}\b", lower):
            found.append(rank)
    if not found:
        return None
    return min(found)


def _score_critical_comment(
    report_text: str,
    issues: list[dict[str, Any]],
    gh_available: bool,
) -> float:
    """
    1.0 - highest-priority open issue has >=2 gh comments (seed + agent addition)
    0.5 - exactly 1 comment on that issue
    0.0 - gh unavailable or no comments
    反例: 只写本地 comment 文件但未发到 GitHub
    """
    if not gh_available or not issues:
        return 0.0
    critical_number = _identify_critical_issue_number(report_text, issues)
    if critical_number is None:
        return 0.0
    comments = _fetch_issue_comments(critical_number)
    if comments is None:
        return 0.0
    count = len(comments)
    if count >= 2:
        return 1.0
    if count == 1:
        return 0.5
    return 0.0


def _identify_critical_issue_number(
    report_text: str, issues: list[dict[str, Any]]
) -> int | None:
    best_number: int | None = None
    best_rank = 10**9
    for issue in issues:
        number = issue.get("number")
        if number is None:
            continue
        window = _item_window(report_text, number)
        rank = _extract_priority_rank(window)
        if rank is None:
            continue
        if rank < best_rank:
            best_rank = rank
            best_number = int(number)
    if best_number is not None:
        return best_number
    if issues:
        return int(issues[0]["number"])
    return None


def _fetch_issue_comments(issue_number: int) -> list[dict[str, Any]] | None:
    return _gh_json(
        [
            "api",
            f"repos/{REPO_SLUG}/issues/{issue_number}/comments",
            "--jq",
            ".",
        ]
    )
