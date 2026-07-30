> Language: **English** · [中文](repair-task-severity-tiers.zh-CN.md)

# Domain Verifier Reference Guide: code/repair-task-severity-tiers

> **domain_id**: `code/repair-task-severity-tiers`
> **category**: Code
> **gate_policy**: strict
> **layer_hint**: mostly-deterministic
> **last_updated**: 260701_agenticjudge_relocate

---

## 1. Task Profile

Code/engineering repair, completion, or config-alignment tasks: comparing the candidate's deliverable against a fixture (the expected configuration/expected code state).

---

## 2. Core Principle (Preventing "Slightly Off Means Total FAIL" Mis-Grading)

Split the must-have fields into two tiers:
- **Core invariants**: if missing, it is a genuine error — score 0.
- **Secondary fields**: by default these are bonus-only; if one truly needs to be treated as a must-have, you must document the rationale in `verifier_summary.md`, and a missing secondary field should only cost half credit (0.5) rather than single-handedly sinking the overall gate (provided all core items are satisfied).

The three categories of permissions/ownership/documentation checks are especially prone to being overly strict: only score 0 against a strict standard (e.g., "owner-only") when the prompt explicitly requires that specific strict form. When there is no explicit requirement, give 0.5 credit for partial compliance — do not require the candidate to guess a strict standard the prompt never stated.

---

## 3. Code Example

```python
def _grade_repair_task(workspace_path, fixture):
    core_signals = {
        "syntax_valid": _check_syntax(workspace_path),          # missing = genuine error: 0.0
        "core_logic_fixed": _check_core_bug_fixed(workspace_path, fixture),
    }
    secondary_signals = {
        "docstring_updated": _check_docstring(workspace_path),   # secondary: missing = 0.5, does not sink the gate
        "permission_mode": _check_permission_mode(workspace_path, fixture),
    }
    core_pass = all(v >= 0.99 for v in core_signals.values())
    secondary_avg = sum(secondary_signals.values()) / max(1, len(secondary_signals))
    return {
        "outcome_passed": core_pass,        # the gate only looks at core
        "score": secondary_avg,
        "breakdown": {**core_signals, **secondary_signals},
    }


def _check_permission_mode(workspace_path, fixture):
    """
    1.0 - permission mode exactly matches the fixture
    0.5 - permission mode is partially compliant (e.g., has an extra/missing strict bit that the prompt didn't explicitly require)
    0.0 - permission mode contradicts the strict form the prompt explicitly required
    """
    required = fixture.get("required_permission_mode")
    actual = _read_permission_mode(workspace_path)
    if required is None:
        return 0.5   # don't score 0 when the prompt didn't explicitly require a strict form
    return 1.0 if actual == required else 0.0
```

---

## 4. Change Log

| Version | Experiment | Change summary |
|---|---|---|
| v1 | 260625 | First discovery of the "slightly off means total FAIL" mis-grading pattern |
| v2 | 260701_agenticjudge | Split out of the unified rules doc into a standalone domain guide |
