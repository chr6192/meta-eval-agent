> Language: **English** · [中文](agent-config.zh-CN.md)

# Domain Verifier Reference Guide: automation-platform/agent-config

> **domain_id**: `automation-platform/agent-config`  
> **category**: Code  
> **gate_policy**: strict  
> **last_updated**: 260630_composer25_baseline

---

## 1. Task Profile

This domain covers: creating or modifying agent skill configuration files (`SKILL.md`, plus optional `cron.yaml` / `channel.yaml`) on automation platforms such as OpenClaw / ClaHub, with fields including `name`, `description`, `channel`, `target-user`, `trigger`, etc.

**Typical task prompt signals**:
- "Create a Skill for XXX"
- "Configure a clawhub / OpenClaw agent"
- "Set up a cron job / channel routing"

---

## 2. Must-Have Predicates

| Predicate | Check method | Counter-example (fail) |
|---|---|---|
| P_skill_md_exists | Filesystem check for `workspace/SKILL.md` | File is missing |
| P_frontmatter_valid | Parse the YAML frontmatter; verify the `name` and `description` fields are non-empty | Frontmatter missing or name="" |
| P_channel_correct | Derive the expected channel value from the task spec and compare it exactly against the `channel:` field in `SKILL.md` | Wrong channel value |
| P_no_forbidden_ops | No high-risk system calls in the transcript (if the task has this constraint) | Agent ran `rm -rf` |

**Gate**: strict (PASS only if every must-have signal is ≥ 0.99)

---

## 3. Applying Rule 17: Prioritize Fixture Ground-Truth Comparison

The correct way to write `P_channel_correct` — first read the expected channel from the task spec file (`task_md.md` frontmatter or inputs/), then compare it against the deliverable:

```python
def _check_channel_correct(workspace_path, task_spec):
    """
    1.0 - the channel field exactly matches the value required by task_spec
    0.5 - the channel field is present but only fuzzily matches (or-guard)
    0.0 - the field is missing or clearly wrong
    # truth-source=task-spec-fixture
    # or-guard: partial → 0.5
    """
    expected_channel = task_spec.get("required_channel")  # read from the fixture, not hardcoded
    if not expected_channel:
        return 0.5   # degrade to 0.5 when the fixture is unavailable, don't block the gate on this alone
    skill_path = Path(workspace_path) / "SKILL.md"
    if not skill_path.exists():
        return 0.0
    content = skill_path.read_text(errors="replace")
    fm = _parse_frontmatter(content)
    actual_channel = fm.get("channel", "")
    if actual_channel == expected_channel:
        return 1.0
    if expected_channel.lower() in actual_channel.lower():
        return 0.5   # or-guard
    return 0.0
```

**Counter-example** (do not write it this way):
```python
# ✗ BAD: directly checks whether the "channel" keyword appears in the file, without comparing it to the expected value
def _check_channel(content):
    return 1.0 if "channel:" in content else 0.0
```

---

## 4. Known Pitfalls

- **Pitfall 1**: Only checking that `SKILL.md` exists, without validating its content (Rule 09: pure existence/substring checks must not earn full marks on their own)  
  → Fix: must parse the frontmatter and validate the key fields

- **Pitfall 2**: Using `if "clawhub" in content` to judge whether the platform is correct  
  → Fix: read the expected platform name from the task spec and compare it exactly

- **Pitfall 3**: Only checking the cron expression's format (`\d{1,2} \d{1,2} ...`), without validating its semantic value  
  → Fix: if the task spec specifies a concrete frequency, compare against the expected cron string

---

## 5. Change Log

| Version | Experiment | Change summary |
|---|---|---|
| v1 | 260625 iter_1 | Initial discovery, `cold_rounds=1` |
| v2 | 260630_composer25 baseline | Expanded the guide format; added the P_channel_correct example |

---

## 6. Layer Assignment

All must-have predicates in this domain can be verified structurally (file existence, frontmatter field values, cron syntax); `layer_hint=mostly-deterministic` and `agentic_judge_dimensions` is empty — there is no need to introduce an agentic_judge call for this domain. If a subjective dimension emerges for this domain in the future (e.g., "whether the skill description's wording is clear"), you must first confirm, via the predicate-triage steps in SKILL.md, that it genuinely cannot be verified structurally before adding it to `agentic_judge_dimensions`; it must not be added by default.
