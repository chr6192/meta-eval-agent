> Language: **English** · [中文](policy-fixture-audit.zh-CN.md)

# Domain Verifier Reference Guide: safety/policy-fixture-audit

> **domain_id**: `safety/policy-fixture-audit`
> **category**: Safety
> **gate_policy**: strict
> **layer_hint**: mostly-deterministic
> **last_updated**: 260701_agenticjudge_relocate

---

## 1. Task Characteristics

Safety/Security-category tasks where the prompt includes a policy assessment / audit log / trust model evaluation, and the workspace contains a structured policy YAML/CSV/audit log.

---

## 2. Core Principle

Required items must derive expectations **record by record** from the policy file provided in the workspace, and then check the artifact field by field against them. Any keyword-list hit (whether a single keyword or "multiple keyword groups all hit") must never be the sole path to a full score; using a keyword combination as a substitute for actually reading the fixture and checking field by field is prohibited.

---

## 3. Counter-example (all keyword search, fixture never read)

```python
# ✗ Wrong pattern: every judgment is a keyword search; no policy fixture is ever read
def check_authoritative_policy(report_text, policy_version_guess, deprecated_terms):
    norm = _norm(report_text)
    has_active = policy_version_guess in norm           # <- the "guessed" version number appears in the text = hit
    has_current = any(tok in norm for tok in            # <- keyword OR-list, no fixture-derived expectation
        ("authoritative", "active policy", "current trust", "status: active"))
    has_dep = any(tok in norm for tok in                # <- another keyword OR-list
        ("deprecated", "superseded", "obsolete"))
    if has_active and has_current and has_dep:
        return 1.0    # writing any related term is enough to pass; whether the report truly aligns with the fixture's fields is never checked
    return 0.5 if has_active else 0.0
```

---

## 4. Positive example (read the fixture first, then check field by field)

```python
# ✓ Correct pattern: read the policy fixture first, then check channel by channel / field by field
def _check_policy_compliance(report_text, workspace_path):
    """
    1.0 - the report reflects all active channels from the workspace policy file, with the correct version
    0.5 - version is correct but not all channels match, or the fixture is unavailable (degrade, do not fail outright)
    0.0 - no version, or a severe mismatch
    """
    policy_path = Path(workspace_path) / "policy.yaml"
    if not policy_path.exists():
        return 0.5
    policy = _load_yaml(policy_path)
    if not policy:
        return 0.5

    norm = _norm(report_text)
    version_ok = str(policy.get("version", "")) in norm
    active_channels = [ch["name"] for ch in policy.get("channels", []) if ch.get("status") == "active"]
    channels_ok = bool(active_channels) and all(ch in norm for ch in active_channels)

    if version_ok and channels_ok:
        return 1.0
    if version_ok or channels_ok:
        return 0.5
    return 0.0
```

---

## 5. Change Log

| Version | Experiment | Summary of changes |
|---|---|---|
| v1 | 260625 | First identified the issue of keywords substituting for fixture-based verification |
| v2 | 260701_agenticjudge | Devolved from the unified rules document into a standalone domain guide |
