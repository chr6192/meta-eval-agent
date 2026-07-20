# Domain Verifier 参考指南：code/gt-recomputation

> **domain_id**: `code/gt-recomputation`
> **category**: Code
> **gate_policy**: strict
> **layer_hint**: mostly-deterministic
> **last_updated**: 260701_agenticjudge_seed

---

## 1. 任务特征

任务有客观正确答案：数值优化、物理仿真、算法结果、财务对账。workspace 输入包含足够的原始数据，可以独立于候选的做法重新计算出期望值。

**典型信号**：Prompt 含"计算"、"求解"、"优化"、"仿真"等词，workspace 有结构化输入文件（CSV/JSON/配置）。

---

## 2. 为什么这个 domain 几乎全走 Deterministic 层

这类任务的"正确答案"是可以**算出来**的，不需要、也不应该用 agentic_judge 去"评估"——那是在用主观判断力去猜一个客观存在的数字。正确做法永远是：写一段独立的计算逻辑，从 workspace 输入重算期望值，再和产物数值做容差对照。这类任务如果做对了，判分结果对候选的措辞/格式变化完全免疫，是所有判分方式里最稳的一种，值得优先投入。

---

## 3. Deterministic 层正例

```python
def _reference_recompute(workspace_path):
    """从 workspace 原始数据独立重算期望值，不依赖候选的计算过程。"""
    raw = _load_raw_data(workspace_path)
    return _domain_specific_formula(raw)


def _numeric_result_matches(workspace_path):
    """
    1.0 - 产物数值与独立重算结果的相对误差 < 1%
    0.5 - 相对误差 1%-5%（容差带，不得单独进必检项闸门）
    0.0 - 误差 > 5% 或产物缺失/不可解析
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

若 Prompt 要求可执行脚本，须叠加"真实执行验证"（见 `meta-rules.md` 的可执行交付物规则）：在 `workspace_path` 上真实执行脚本，取运行时输出与重算值比对，而不是只做静态数值检查。

---

## 4. 已知陷阱

- **反面模式**：把数值判断退化成"报告里是否出现某数字"的子串检查——容易被凑巧写对的数字或格式变体骗过/漏过。
- **不要为"计算过程是否合理"引入 agentic_judge**：先问"这个中间过程是不是也能从原始数据验证"——大多数情况下答案是"能"，应该写成 Deterministic 层的多步骤数值检查。真正没法结构化验证的（如"解题思路的清晰表达"）才允许极少量加分项性质的 agentic_judge 信号，且不得进必检项。

---

## 5. 迭代记录

| 版本 | 实验 | 改动摘要 |
|---|---|---|
| v1 | 260701_agenticjudge seed | 初始创建 |
