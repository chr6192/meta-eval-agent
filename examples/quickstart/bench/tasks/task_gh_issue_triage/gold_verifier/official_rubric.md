## Expected Behavior

The agent should:

1. Use gh CLI to list and read issues and PRs
2. Analyze each item for urgency and impact
3. Comment on the most critical issue
4. Write a structured triage report to `triage_report.md`

This tests the agent's ability to use the gh CLI for a multi-step GitHub workflow: list, read, comment, and synthesize.

## Grading Criteria

- [ ] Agent listed issues using gh
- [ ] Agent listed or viewed PRs using gh
- [ ] Agent read individual issues/PRs to understand content
- [ ] Agent commented on the most critical issue
- [ ] File `triage_report.md` created in workspace
- [ ] All open items are present in the report
- [ ] Each item has a priority assigned
- [ ] Report is sorted by priority

## LLM Judge Rubric

### Criterion 1: gh CLI Usage (Weight: 30%)

**Score 1.0**: Agent fluently used gh CLI to list, view, and comment on issues/PRs with correct parameters.
**Score 0.75**: Agent used gh CLI correctly but with minor parameter issues.
**Score 0.5**: Agent used some gh commands but struggled with syntax.
**Score 0.25**: Agent barely used gh CLI.
**Score 0.0**: Agent did not use gh CLI at all.

### Criterion 2: Triage Quality (Weight: 40%)

**Score 1.0**: All items correctly prioritized with accurate analysis and specific recommendations.
**Score 0.75**: Most items correctly prioritized with reasonable analysis.
**Score 0.5**: Some items prioritized but notable errors in judgment.
**Score 0.25**: Priority assignments are mostly incorrect or missing.
**Score 0.0**: No meaningful triage performed.

### Criterion 3: Comment Quality (Weight: 30%)

**Score 1.0**: Comment on the right issue with insightful analysis and actionable next steps.
**Score 0.75**: Comment targets the right issue with reasonable suggestions.
**Score 0.5**: Comment created but targets a less appropriate issue or is generic.
**Score 0.25**: Comment created but with irrelevant content.
**Score 0.0**: No comment created.
