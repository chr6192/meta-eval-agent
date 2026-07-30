> Language: **English** · [中文](gt-recomputation.zh-CN.md)

# Domain Verifier Reference Guide: code/gt-recomputation

> **domain_id**: `code/gt-recomputation`
> **category**: Code
> **gate_policy**: strict
> **layer_hint**: mostly-deterministic
> **last_updated**: 260701_agenticjudge_seed

---

## 1. Task Profile

Tasks with an objectively correct answer: numerical optimization, physics simulation, algorithmic results, financial reconciliation. The workspace inputs contain enough raw data to recompute the expected value independently of the candidate's approach.

**Typical signals**: the prompt contains words like "compute", "solve", "optimize", "simulate"; the workspace has structured input files (CSV/JSON/config).

---

## 2. Why This Domain Runs Almost Entirely on the Deterministic Layer

The "correct answer" for this type of task can be **computed**, so there is no need — and it would be wrong — to use agentic_judge to "assess" it; that amounts to using subjective judgment to guess at an objectively existing number. The correct approach is always: write an independent computation routine that recomputes the expected value from the workspace inputs, then compare it against the deliverable's value within a tolerance. Done correctly, this type of grading is completely immune to changes in the candidate's wording or formatting, making it the most robust of all grading approaches and one worth prioritizing.

---

## 3. Deterministic-Layer Good Example

```python
def _reference_recompute(workspace_path):
    """Independently recompute the expected value from the workspace's raw data, without depending on the candidate's computation."""
    raw = _load_raw_data(workspace_path)
    return _domain_specific_formula(raw)


def _numeric_result_matches(workspace_path):
    """
    1.0 - the deliverable's value has a relative error < 1% versus the independently recomputed result
    0.5 - relative error is 1%-5% (tolerance band; must not gate the must-have check on its own)
    0.0 - error > 5%, or the deliverable is missing/unparseable
    """
    expected = _reference_recompute(workspace_path)
    actual = _extract_result_from_deliverable(workspace_path)
    if actual is None:
        return 0.0
    rel_err = abs(actual - expected) / max(abs(expected), 1e-9)
    if rel_err < 0.01:
        return 1.0
    if rel_err < 0.05:
        return 0.5
    return 0.0
```

If the prompt requires an executable script, you must additionally apply "real execution verification" (see the executable-deliverable rules in `meta-rules.md`): actually execute the script against `workspace_path` and compare its runtime output to the recomputed value, rather than only performing a static numeric check.

---

## 4. Known Pitfalls

- **Anti-pattern**: degrading the numeric check into a substring check for "does this number appear somewhere in the report" — this is easily fooled (or misses a genuine failure) by a number that happens to be right, or by a formatting variant.
- **Do not introduce agentic_judge for "is the computation process reasonable"**: first ask "can this intermediate step also be verified from the raw data" — in most cases the answer is "yes", and it should be written as a multi-step numeric check in the Deterministic layer. Only things that truly cannot be verified structurally (e.g., "clarity of the explanation of the solution approach") may receive a very small, bonus-only agentic_judge signal, and such a signal must never be placed in the must-have set.

---

## 5. Change Log

| Version | Experiment | Change summary |
|---|---|---|
| v1 | 260701_agenticjudge seed | Initial creation |
