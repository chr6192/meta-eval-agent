> Language: **English** · [中文](per-record-fixture-check.zh-CN.md)

# Domain Verifier Reference Guide: office/per-record-fixture-check

> **domain_id**: `office/per-record-fixture-check`
> **category**: Office
> **gate_policy**: strict
> **layer_hint**: mostly-deterministic
> **last_updated**: 260701_agenticjudge_relocate

---

## 1. Task characteristics

Office/Productivity/CRM-type tasks: the deliverable needs to be checked record-by-record against a structured fixture (CSV/JSON ledgers, CRM exports, etc.).

---

## 2. Core principle

The full-score path for a must-pass criterion must **first** derive each record's expected value from the workspace input file, and **then** perform a record-by-record/field-by-field check on the deliverable. Any implementation that substitutes an overall hit ratio ("80% match counts as passing") for a per-record check is capped at 0.5 and cannot pass the must-pass gate on its own. For tasks involving multiple deliverables, check each one independently — do not merge them with OR logic ("passing if any one of them is correct").

---

## 3. Positive example (derive expectations from the fixture first, then check record-by-record with AND logic)

```python
# ✓ Correct pattern: fixture-first + per-record checking
def grade(transcript, workspace_path):
    expected = _derive_expected_from_workspace(workspace_path)
    signals = {}
    signals["exception_classification"] = _score_exception_classification(
        _read_report_text(workspace_path), expected,
    )
    ...


def _derive_expected_from_workspace(workspace_path):
    """Read the expected classification and values for all records from the workspace CSV/JSON fixture."""
    fix_dir = _locate_fixture_dir(workspace_path)
    if fix_dir is None:
        return {"records": [], "record_count": 0}
    crm = _read_indexed_csv(fix_dir / "crm_export.csv", "transaction_id")
    bank = _read_indexed_csv(fix_dir / "bank_settlements.csv", "external_ref")
    records = _classify_records(crm, bank)
    return {"records": records, "record_count": len(records)}


def _score_exception_classification(report_text, expected):
    """
    1.0 - every fixture record has the correct classification label found in the report
    0.5 - at least half of the records are correctly classified (must not pass the must-pass gate on its own)
    0.0 - fewer than half
    """
    hits = 0
    for rec in expected["records"]:
        window = _best_window_for_record(report_text, rec)
        if _category_in_text(window, rec["category"]):
            hits += 1
    ratio = hits / max(1, len(expected["records"]))
    if ratio >= 1.0:
        return 1.0
    if ratio >= 0.5:
        return 0.5
    return 0.0
```

---

## 4. Negative example (making an overall-ratio judgment directly on the deliverable text)

```python
# ✗ Incorrect pattern: doesn't derive expectations from the fixture, judges the deliverable text by ratio directly
def _check_risk_accounts(report_text, accounts):
    # Problem 1: accounts may be a hardcoded list embedded in the grader, not read from the workspace input
    # Problem 2: `name in report_text` is a substring hit, not an exact field check
    matched = sum(1 for a in accounts if str(a["name"]) in report_text)
    ratio = matched / max(1, len(accounts))
    if ratio >= 1.0:
        return 1.0
    if ratio >= 0.5:
        return 0.5   # under a lenient gate, this 0.5 could let a clearly unqualified deliverable pass the gate
    return 0.0
```

---

## 5. Change Log

| Version | Experiment | Summary of changes |
|---|---|---|
| v1 | 260625 | First identified the issue of overall-ratio judgments substituting for per-record checks |
| v2 | 260701_agenticjudge | Split out from the unified rules doc into a standalone domain guide |
