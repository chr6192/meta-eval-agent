# Domain Verifier 参考指南：office/per-record-fixture-check

> **domain_id**: `office/per-record-fixture-check`
> **category**: Office
> **gate_policy**: strict
> **layer_hint**: mostly-deterministic
> **last_updated**: 260701_agenticjudge_relocate

---

## 1. 任务特征

Office/Productivity/CRM 类任务：产物需要与结构化 fixture（CSV/JSON 台账、CRM 导出等）逐条记录核对。

---

## 2. 核心原则

必检项的满分路径必须**先**从 workspace 输入文件推导出每条记录的期望值，**再**在产物上做逐记录/逐字段核对。任何用整体命中比例（"80% 匹配即算过"）替代逐条核对的写法，命中上限只能是 0.5，不能单独进必检项闸门。涉及多份交付物的任务，每份独立核对，不能用"任一份对了就算过"的 OR 逻辑合并通过。

---

## 3. 正例（先从 fixture 推导期望，再逐记录 AND 核对）

```python
# ✓ 正确模式：fixture 先行 + 逐记录核对
def grade(transcript, workspace_path):
    expected = _derive_expected_from_workspace(workspace_path)
    signals = {}
    signals["exception_classification"] = _score_exception_classification(
        _read_report_text(workspace_path), expected,
    )
    ...


def _derive_expected_from_workspace(workspace_path):
    """从 workspace CSV/JSON fixture 读出所有记录的期望分类和数值。"""
    fix_dir = _locate_fixture_dir(workspace_path)
    if fix_dir is None:
        return {"records": [], "record_count": 0}
    crm = _read_indexed_csv(fix_dir / "crm_export.csv", "transaction_id")
    bank = _read_indexed_csv(fix_dir / "bank_settlements.csv", "external_ref")
    records = _classify_records(crm, bank)
    return {"records": records, "record_count": len(records)}


def _score_exception_classification(report_text, expected):
    """
    1.0 - 每条 fixture 记录在报告中都能找到正确的分类标注
    0.5 - 至少一半记录被正确分类（不得单独进必检项闸门）
    0.0 - 少于一半
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

## 4. 反例（直接在产物文本上做整体比例判断）

```python
# ✗ 错误模式：未从 fixture 推导期望，直接对产物文本做比例判断
def _check_risk_accounts(report_text, accounts):
    # 问题1：accounts 可能是 grader 内嵌的硬编码列表，不是从 workspace 输入读的
    # 问题2：name in report_text 是子串命中，不是字段精确核对
    matched = sum(1 for a in accounts if str(a["name"]) in report_text)
    ratio = matched / max(1, len(accounts))
    if ratio >= 1.0:
        return 1.0
    if ratio >= 0.5:
        return 0.5   # 在宽松闸门下，这个 0.5 可能让明显不合格的产物也过闸
    return 0.0
```

---

## 5. 迭代记录

| 版本 | 实验 | 改动摘要 |
|---|---|---|
| v1 | 260625 | 首次发现整体比例判断代替逐记录核对的问题 |
| v2 | 260701_agenticjudge | 从统一规则文档下放为独立 domain guide |
