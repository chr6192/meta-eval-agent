# Rubric: Remote Work Blog Post

Task: Write a ~500-word blog post about benefits of remote work for software developers; save to `blog_post.md`.

## Must-have criteria (deterministic gate)

| Key | Criterion | Pass threshold |
|-----|-----------|----------------|
| `deliverable_exists` | `blog_post.md` exists as a file at the workspace root (per prompt) | score ≥ 0.99 |
| `deliverable_substantial` | File contains more than 50 characters of non-empty content | score ≥ 0.99 |
| `word_count_near_500` | Word count is 450–550 tokens (±10% of 500) | score ≥ 0.99 |

**Gate rule:** `outcome_passed = True` only when all must-have criteria meet threshold. Agentic-judge dimensions do not affect pass/fail.

## Nice-to-have criteria (score only)

| Key | Criterion | Scoring |
|-----|-----------|---------|
| `topic_anchors_present` | Text mentions remote-work context, software-developer audience, and benefit framing (keyword anchors; capped structural signal) | 1.0 / 0.5 / 0.0 |
| `agentic_judge_topic_benefits_remote_work_developers` | Post substantively discusses multiple benefits of remote work for software developers with real arguments | 0.0–1.0 |
| `agentic_judge_narrative_coherence` | Reads as a coherent blog post with logical flow and no major contradictions | 0.0–1.0 |

**Overall score:** arithmetic mean of `topic_anchors_present`, `word_count_near_500` (including partial credit when gate fails), and both agentic_judge dimensions. If agentic judge is unavailable, those dimensions score 0.0.

## Failure examples

- Saves only to a subdirectory, not root `blog_post.md` → `deliverable_exists` = 0
- Empty file or title-only stub → `deliverable_substantial` < 0.99
- 300-word or 700-word essay → `word_count_near_500` < 0.99
- Generic office essay with no developer focus → low `topic_benefits_remote_work_developers` (score impact only)
