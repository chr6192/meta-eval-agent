# Rubric: GitHub Issue Triage (`testuser/my-project`)

## Overview

Agent must use `gh` to review open issues/PRs, comment on the most critical issue, and deliver `triage_report.md` with per-item priority, category, and recommended action sorted by priority.

## Criteria (maps 1:1 to `grader.py` breakdown keys)

### Must-have (deterministic gate)

| Key | Weight in gate | Pass threshold | Description |
|-----|----------------|----------------|-------------|
| `report_file_exists` | required | ≥0.99 | `triage_report.md` exists in workspace and contains substantive content (>100 chars). |
| `all_items_covered` | required | ≥0.99 | Every open issue and PR returned by `gh` at grade time is referenced by number and title tokens in the report. |
| `required_fields_per_item` | required | ≥0.99 | Each covered item's local section includes priority, category, and recommended action markers. |
| `priority_sorted` | required | ≥0.99 | Items appear in non-increasing priority order (critical/high before low). |
| `critical_issue_comment_posted` | required | ≥0.99 | The highest-priority open issue has ≥2 comments on GitHub (pre-existing seed comment + agent's new comment). |

### Nice-to-have (score only, agentic_judge)

| Key | Description |
|-----|-------------|
| `agentic_judge_critical_comment_substantive` | Comment on the critical issue contains concrete analysis and actionable next steps tied to that issue. |
| `agentic_judge_triage_reasoning_coherent` | Priority assignments and recommended actions in the report are logically consistent with each item's described impact. |

## Gate formula

`outcome_passed = ALL(must_have signals ≥ 0.99)`. Continuous `score` is the mean of agentic_judge dimensions when available.

## Scoring tiers (deterministic signals)

- **1.0** — requirement fully met per signal docstring
- **0.5** — partial coverage (per-item signals only; cannot pass gate at 0.5)
- **0.0** — missing, wrong, or fixture/API unavailable
