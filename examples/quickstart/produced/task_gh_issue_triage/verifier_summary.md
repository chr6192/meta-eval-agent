# Verifier Summary: GitHub Issue Triage

## Step 0 · Domain

Task keywords matched `code/repair-task-severity-tiers` (`fix` in seed issue/PR titles). Per-item triage structure aligns with `office/per-record-fixture-check` patterns (inferred, no keyword hit). Read both guides; truth is fetched via `gh` API, not embedded fixture files.

## Atomic Predicates

| ID | Track | Breakdown key | Description |
|----|-------|---------------|-------------|
| P1 | 确定性 | `report_file_exists` | `triage_report.md` present and non-trivial |
| P2 | 确定性 | `all_items_covered` | All open issues/PRs from `gh` referenced in report |
| P3 | 确定性 | `required_fields_per_item` | Each item section has priority, category, recommended action |
| P4 | 确定性 | `priority_sorted` | Higher-priority items appear before lower-priority ones |
| P5 | 确定性 | `critical_issue_comment_posted` | Top-priority issue has ≥2 GitHub comments (agent added one) |
| P6a | agentic_judge | `agentic_judge_critical_comment_substantive` | Critical-issue comment analysis quality |
| P6b | agentic_judge | `agentic_judge_triage_reasoning_coherent` | Report triage reasoning coherence |

**Counts:** 7 predicates (确定性 5 / agentic_judge 2)

## Ambiguity Decisions

| ID | Choice | Rationale |
|----|--------|-----------|
| Amb-1 | Gate uses live `gh` API, not hardcoded seed titles | Fixture truth must come from environment at grade time (rule 17); avoids leaking seed literals |
| Amb-2 | Critical comment: require ≥2 comments on top issue | Task seed notes one pre-existing comment on #1; second comment implies agent posted |
| Amb-3 | Title match: number + ≥50% title tokens | Balances strict fixture alignment vs minor formatting variance |
| Amb-4 | Priority sort: parse text ranks, allow one inversion at 0.5 | Reports may group by section headers; strict zero-inversion too brittle |
| Amb-5 | agentic_judge only for analysis quality, not coverage | Coverage is structurally checkable against `gh` output |

## Data Sources (rule 14)

| Signal | Source |
|--------|--------|
| P1 | workspace deliverable `triage_report.md` |
| P2–P4 | `gh issue/pr list` + workspace report |
| P5 | `gh api .../issues/{n}/comments` |
| P6a–P6b | workspace + transcript via `invoke_agentic_judge` |

## Gate Policy

- **gate:** strict deterministic (all 5 must-have signals ≥0.99)
- **basis:** ≥1 structurally checkable must-have predicates (rule 15); PASS never depends on agentic_judge alone

## Self-reflection

### Round 1
- Decomposed from Prompt before reading candidates.
- Opened candidates: most simulated wrong issue sets when `gh` unavailable; 4/8 produced `triage_report.md`.

### Round 2
- Tightened P2 to require title tokens, not number-only (anti keyword-shell pass).
- Kept comment check outcome-based via `gh` API, not transcript process (rule 18).

### Mental prediction (gh unavailable in sandbox)

| Candidate | report | coverage | fields | sort | comment | PASS |
|-----------|--------|----------|--------|------|---------|------|
| qwen3.7-max | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | FAIL |
| qwen3.6-plus | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | FAIL |
| glm-5.1 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | FAIL |
| qwen3.6-27b | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | FAIL |
| others (no report) | 0.0 | … | … | … | … | FAIL |

**Distribution:** PASS=0 FAIL=8 — no all-pass over-width.

### Checklist

| Check | Result |
|-------|--------|
| 过宽 | ✓ (0/8 PASS in sandbox) |
| 判别力 | ✓ (delete report → P1 fail) |
| fixture真值 | ✓ (`gh` API first, not hardcoded titles) |
| 过程信号 | ✓ (no transcript-only must-have) |
| 可执行验证 | ✓ (`gh` subprocess on grade host) |
| agentic_judge关键词近似 | ✓ |
| 接地 | ✓ (dimensions map to P6a/P6b) |
| 回流泄漏 | ✓ (coverage stays deterministic) |
| 分数拉开度 | ✓ (report-only ~0.2 vs no-report 0.0) |
| 未读答案 | ✓ |
| 不过拟合 | ✓ (no candidate paths/names) |
| stdlib only | ✓ (+ judge_harness) |

## Domain Note

- matched_domain: [`code/repair-task-severity-tiers`]
- inferred_domain: `office/per-record-fixture-check` (per-item triage without keyword hit)
- key_pitfalls_hit: ["未从 fixture/API 读真值而硬编码标题", "用关键词 OR 代替逐条 issue 核对"]
- guide_useful: yes
