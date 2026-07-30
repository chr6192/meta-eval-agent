> Language: **English** · [中文](deep-verifiable-check.zh-CN.md)

# Domain Verifier Reference Guide: multimodal/deep-verifiable-check

> **domain_id**: `multimodal/deep-verifiable-check`
> **category**: Multimodal
> **gate_policy**: strict-if-checkable
> **layer_hint**: mixed
> **last_updated**: 260701_agenticjudge_relocate

---

## 1. Task characteristics

Creative/Score/Synthesis/Multimodal-type tasks, where deliverables include SVG/HTML/sheet-music/chart files.

---

## 2. Core principle

At least one must-pass criterion must perform a **numeric-level or execution-level** check: read the expected values/specs from the workspace input, and compare them against the parsed deliverable within tolerance; or run a reproducible, executable check on the deliverable (parse the DOM/path data and verify key measurements). Signals that only do surface structural checks like "file exists + element count + text anchor" are capped at 0.5, and combining multiple surface checks cannot substitute for a deep check.

Subjective judgments about aesthetics/layout ("does this chart look good") go through agentic_judge (see this domain's `agentic_judge_dimensions`) — don't force them into a keyword check.

---

## 3. Code example

```python
def _deep_numeric_check(workspace_path):
    """
    1.0 - key measurements parsed from the SVG/HTML (coordinates, numeric labels) match the
          workspace input spec within tolerance
    0.5 - the element structure exists but the values deviate
    0.0 - elements are missing or values deviate severely
    """
    expected_values = _load_expected_from_workspace(workspace_path)
    parsed = _parse_svg_or_html(workspace_path)
    if parsed is None:
        return 0.0
    diffs = [abs(parsed.get(k, 0) - v) for k, v in expected_values.items()]
    if all(d < 0.05 * abs(v) for d, v in zip(diffs, expected_values.values())):
        return 1.0
    if parsed:
        return 0.5
    return 0.0


def _surface_structure_check(workspace_path):
    """
    Only counts element count/tag names/text anchors — capped at 0.5 on its own,
    must be combined with _deep_numeric_check, cannot replace it.
    """
    ...
```

For the agentic_judge portion (layout/aesthetic dimensions), follow the pattern in `creative/narrative-quality.md`, swapping the `judge_question` for "is this visualization's layout clear and does it achieve its presentation purpose" — the schema and invocation stay the same.

---

## 4. Change Log

| Version | Experiment | Summary of changes |
|---|---|---|
| v1 | 260625 | First identified the issue of surface structural checks substituting for deep checks |
| v2 | 260701_agenticjudge | Split out from the unified rules doc into a standalone domain guide; added agentic_judge dimensions |
