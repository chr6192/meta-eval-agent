> Language: **English** · [中文](workspace-execution.zh-CN.md)

# Domain Verifier Reference Guide: code/workspace-execution

> **domain_id**: `code/workspace-execution`
> **category**: Code
> **gate_policy**: strict
> **layer_hint**: mostly-deterministic
> **last_updated**: 260701_agenticjudge_relocate

---

## 1. Task Profile

The prompt requires producing a runnable script, shell command, or executable workflow, and the resulting behavior needs to be verified by actually running it.

---

## 2. Core Principle

Execution verification must run against the candidate's own passed-in `workspace_path`. It is **forbidden** for the grader to build its own temporary directory internally, fabricate a test scenario, and run against that fake scenario instead. The expected result must be derived dynamically from the workspace's input files, not hardcoded.

---

## 3. Counter-Example (Building a Fake Test Environment, Which Makes the Grade Unrelated to the Candidate's Actual Deliverable)

```python
# ✗ Wrong pattern: the grader builds a temporary directory to impersonate the workspace
def _executable_behavior_signal(command_text, workspace_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        _build_fake_scene(Path(tmpdir))       # ← the grader fabricates a file tree in tmpdir
        result = subprocess.run(
            ["sh", "-c", command_text],
            cwd=tmpdir,                        # ← runs against the fabricated scenario, unrelated to the candidate's real workspace
            capture_output=True, timeout=30,
        )
        got = set(_parse_output_paths(result.stdout.decode()))
        expected = _reference_matches(Path(tmpdir))  # ← the expected value is also computed on the fake scenario
        return 1.0 if got == expected else 0.0
# Problem: the candidate's command succeeding on this fabricated scenario does not mean it is correct on the candidate's real workspace
```

---

## 4. Good Example (Deriving the Expected Result From, and Executing Against, the Real workspace_path)

```python
# ✓ Correct pattern: derive expectations from the workspace inputs, execute against the candidate's real workspace_path
def _executable_behavior_signal(command_text, workspace_path):
    """
    1.0 - the command executes in the candidate's workspace, and the set of output paths exactly matches the expectation derived from the workspace contents
    0.5 - the command runs, but the output set deviates from the expectation
    0.0 - execution fails or produces no output
    """
    expected = _derive_expected_from_workspace_inputs(workspace_path)
    if expected is None:
        return 0.5   # degrade rather than scoring 0 outright when the fixture is unavailable

    result = subprocess.run(
        ["sh", "-c", command_text],
        cwd=workspace_path,             # ← runs against the candidate's actual workspace, not a temp directory
        capture_output=True, timeout=30,
    )
    if result.returncode != 0:
        return 0.0

    got = set(_parse_output_paths(result.stdout.decode()))
    if got == expected:
        return 1.0
    if got & expected:
        return 0.5
    return 0.0


def _derive_expected_from_workspace_inputs(workspace_path):
    """Derive the expected output from the workspace inputs (the objects described in the task spec), rather than a value hardcoded in the grader."""
    root = Path(workspace_path)
    if not root.is_dir():
        return None
    matches = set()
    for f in root.rglob("*.log"):
        try:
            if "FATAL:" in f.read_text(errors="replace"):
                matches.add(str(f.relative_to(root)))
        except OSError:
            pass
    return matches if matches else None
```

---

## 5. Change Log

| Version | Experiment | Change summary |
|---|---|---|
| v1 | 260625 | First discovery of the fake-scenario problem |
| v2 | 260701_agenticjudge | Split out of the unified rules doc into a standalone domain guide |
