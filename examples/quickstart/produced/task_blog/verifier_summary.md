# Verifier Summary: Blog Post Writing (Remote Work)

## Step 0 · Domain

- Registry keyword scan on task text: no `domains/registry.json` keyword hit (English prompt).
- Inferred type: creative narrative / blog writing → consulted `creative/narrative-quality` guide as prior.

## Atomic Predicates

| ID | Track | Description |
|----|-------|-------------|
| P1 | 确定性 | Workspace root contains `blog_post.md` (prompt-specified deliverable path) |
| P2 | 确定性 | Deliverable non-empty (>50 chars) |
| P3 | 确定性 | Word count 450–550 tokens (±10% of 500) |
| P4a | 确定性 (nice) | Topic anchors: remote work + software developers + benefits framing |
| P4b | agentic_judge | Substantively discusses benefits of remote work for software developers |
| P5 | agentic_judge | Coherent blog narrative with logical flow |

**Breakdown keys:** `deliverable_exists`, `deliverable_substantial`, `word_count_near_500`, `topic_anchors_present`, `agentic_judge_topic_benefits_remote_work_developers`, `agentic_judge_narrative_coherence`

## Step 1.1 · Triage Table

```
P1 [确定性] blog_post.md at workspace root
P2 [确定性] substantial non-empty content
P3 [确定性] ~500 word count (450–550)
P4 [拆分]
  → P4a [确定性/nice] topic keyword anchors (capped; not gate)
  → P4b [agentic_judge] substantive benefit discussion for devs
P5 [agentic_judge] narrative coherence
```

## Step 1.5 · Ambiguity Decisions

| ID | Choice | Reason |
|----|--------|--------|
| Amb-1 | Word count 450–550 (±10%) | "500-word" conventionally means approximate length, not exact |
| Amb-2 | Deliverable must be workspace-root `blog_post.md` | Prompt literal path; subdirectory-only copy insufficient |
| Amb-3 | Markdown headings optional | Prompt asks for blog post prose, not a fixed schema |

## Data Sources (rule 14)

| Signal | Source |
|--------|--------|
| P1–P4a | `workspace_path/blog_post.md` (candidate deliverable) |
| P4b, P5 | agentic_judge reads sandbox copy of workspace deliverable |
| transcript | Passed through to judge harness; not used in deterministic gate |

## Gate Policy

- **gate:** `deterministic-must-have-all` (not pure-agentic_judge)
- **must_have:** `deliverable_exists`, `deliverable_substantial`, `word_count_near_500` — all must be ≥0.99
- **score-only:** `topic_anchors_present`, `word_count_near_500` (partial credit in score), both agentic_judge dimensions
- **Rationale:** Deliverable path, non-emptiness, and approximate length are structurally checkable; topical depth and writing quality require semantic judgment (domain guide: mostly-agentic-judge for quality, deterministic anchors for existence/length).

## Self-reflection (Round 1–2)

### Mental run (deterministic + score without live judge)

| Candidate | Gate | wc | anchors | est. score (judge=0) |
|-----------|------|-----|---------|----------------------|
| kimi-k2.6 | PASS | 1.0 | 1.0 | 0.50 |
| qwen3.6-27b | PASS | 1.0 | 1.0 | 0.50 |
| qwen3.6-max-preview | PASS | 1.0 | 1.0 | 0.50 |
| glm-5.1 | FAIL | 0.0 | 1.0 | 0.25 |
| qwen3.6-35b-a3b | FAIL | 0.5 | 1.0 | 0.375 |
| qwen3.6-plus | FAIL | 0.0 | 1.0 | 0.25 |
| qwen3.7-max | FAIL | 0.5 | 1.0 | 0.375 |
| qwen3.7-plus | FAIL | 0.5 | 1.0 | 0.375 |

**Distribution:** PASS=3, FAIL=5 (not all-pass ✓)

**Score spread:** PASS avg 0.50 vs FAIL avg ~0.31 → range 0.19 ≥ 0.15 ✓

### Discrimination tests

- Delete `blog_post.md` on PASS workspace → `deliverable_exists=0` → FAIL ✓
- Truncate PASS post to ~100 words → `word_count_near_500=0` → FAIL ✓
- Replace body with unrelated topic (no remote/dev) → `topic_anchors_present` drops → lower score ✓

### Checklist

| Check | Result |
|-------|--------|
| 过宽 | ✓ (5/8 FAIL on word count) |
| 判别力 | ✓ (deletion/truncation flips gate) |
| fixture真值 | n/a (no workspace input fixture) |
| 过程信号 | ✓ (transcript not in gate) |
| 可执行验证 | n/a |
| agentic关键词近似 | ✓ (invoke_agentic_judge only) |
| 接地 | ✓ (schema maps to P4b/P5) |
| 回流泄漏 | ✓ (topic substance not keyword-gated) |
| mutation | ✓ (quality dims via judge; length/topic anchors degrade on edit) |
| 分数拉开度 | ✓ |
| 未读答案 | ✓ |
| 不过拟合 | ✓ |
| stdlib only | ✓ |
| judge_harness 拷贝 | ✓ (byte-identical diff) |

## Domain Note

- matched_domain: []
- inferred_domain: creative/narrative-quality
- key_pitfalls_hit: ["避免关键词密度冒充语义质量——P4b/P5 走 agentic_judge", "agentic_judge 维度不进 must-have 闸门"]
- guide_useful: n-a
