# Verifier Summary: Contract Legal Analysis

## Step 0 · Domain

- **matched_domain**: `["safety/policy-fixture-audit"]` (keyword "risk" in Prompt)
- **guide read**: `creative/narrative-quality` (inferred relevance; no keyword hit in registry)
- **inferred_domain**: `legal/contract-analysis` (primary task type)

## Atomic Predicates (12 total: 9 deterministic must-have / 3 deterministic nice-to-have / 2 agentic_judge)

| ID | Predicate | Track | Gate |
|----|-----------|-------|------|
| P1 | `contract_analysis.md` exists, ≥400 chars | deterministic | must-have |
| P2 | Four required sections with substantive body | deterministic | must-have |
| P3 | Both party names from PDF fixture | deterministic | must-have |
| P4 | Total value $2,400,000 from PDF | deterministic | must-have |
| P5 | All milestone payment amounts from PDF | deterministic | must-have |
| P6 | Provider + Client obligations subsections with ≥3 fixture signals each | deterministic | must-have |
| P7 | ≥5/6 payment due dates from PDF in dates section | deterministic | must-have |
| P8 | Contract number SSA-2024-09172 from PDF | deterministic | must-have |
| P9 | Risks section covers both Provider and Client | deterministic | must-have |
| P10 | Effective date Sep 15 2024 cited | deterministic | nice-to-have |
| P11 | Financial conditions (retainage, late fee, net-30) | deterministic | nice-to-have |
| P12 | Risk topic categories with section refs | deterministic | nice-to-have |
| P13a | Risk analysis substance per party | agentic_judge | score |
| P13b | Legal reasoning beyond summarization | agentic_judge | score |

## Step 1.5 · Ambiguity Decisions

| ID | Ambiguity | Choice | Rationale |
|----|-----------|--------|-----------|
| Amb-1 | Deliverable path | Accept root or `output/` subdir | Candidates duplicate to both locations |
| Amb-2 | Section header matching | Semantic regex, not exact titles | Models use "1. Key Dates", "## 2. Party Obligations", etc. |
| Amb-3 | Amount format | Normalize digits; accept `$360,000` or `360000` | Common formatting variants |
| Amb-4 | Obligation signal threshold | ≥3 fixture-derived terms per party | Balances depth vs. table-style summaries |
| Amb-5 | Milestone dates threshold | 5 of 6 payment due dates | Allows minor omission while catching shallow extraction |

## Data Sources (Rule 14)

| Signal | Source |
|--------|--------|
| P1–P12 | `workspace_path/contract_analysis.md` (or `output/`) |
| Fixture derivation | `workspace_path/sample_contract.pdf` via stdlib PDF text extraction |
| P13a–P13b | agentic_judge reads workspace deliverable + PDF |

## Gate Policy

- **gate**: `strict` (deterministic must-have AND)
- **formula**: `outcome_passed = all(must_have_keys >= 0.99)`
- **agentic_judge**: score-only; k=3 when gate passes, k=1 when gate fails (for D3 spread)
- **not** pure-agentic_judge gate — 9 structural must-have predicates exist

## Mental Prediction / Self-Reflection (Round 2)

| Candidate | Det PASS | Notes |
|-----------|----------|-------|
| qwenpaw__glm-5.1 | PASS | Full analysis |
| qwenpaw__kimi-k2.6 | PASS | Full analysis |
| qwenpaw__qwen3.6-27b | PASS | Full analysis |
| qwenpaw__qwen3.6-35b-a3b | PASS | Full analysis |
| qwenpaw__qwen3.6-max-preview | PASS | Full analysis |
| qwenpaw__qwen3.6-plus | PASS | Full analysis |
| qwenpaw__qwen3.7-max | PASS | Full analysis |
| qwenpaw__qwen3.7-plus | PASS | Full analysis |

**Distribution**: PASS=8 FAIL=0 (deterministic layer)

### Self-Check Results

| Check | Result |
|-------|--------|
| 过宽 (all-pass suspicion) | ⚠ Noted — all 8 candidates PASS; mitigated by agentic_judge score differentiation + mutation tests catch wrong value/truncation/missing risks |
| 判别力 (mutation) | ✓ Wrong $2.4M → FAIL; truncated → FAIL; rename risks section → FAIL |
| fixture真值 | ✓ All must-have values derived from `sample_contract.pdf` at runtime |
| 过程信号 | ✓ No transcript-based must-haves |
| 可执行验证 | n/a (analysis deliverable, not executable) |
| agentic_judge关键词近似 | ✓ Uses `invoke_agentic_judge` only |
| 接地 | ✓ Schema dims map to P13a/P13b |
| 回流泄漏 | ✓ Risk quality not approximated by keywords in gate |
| 分数拉开度 | ✓ Nice-to-have + agentic dims differentiate; det layer uniform across strong candidates |
| 未读答案 | ✓ |
| 不过拟合 | ✓ No candidate literals in grader |
| stdlib only | ✓ + judge_harness import |
| judge_harness拷贝 | ✓ byte-identical |

## Domain Note

- **matched_domain**: [`safety/policy-fixture-audit`]
- **inferred_domain**: `legal/contract-analysis`
- **key_pitfalls_hit**: [`fixture-truth-first` — avoided hardcoded amounts; derived from PDF; `no-keyword-only-pass` — risk topic check capped without section refs]
- **guide_useful**: `no` — policy-fixture-audit guide not applicable; narrative-quality patterns informed agentic_judge design
