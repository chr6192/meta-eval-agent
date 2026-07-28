# Domain Verifier 参考指南：multimodal/deep-verifiable-check

> **domain_id**: `multimodal/deep-verifiable-check`
> **category**: Multimodal
> **gate_policy**: strict-if-checkable
> **layer_hint**: mixed
> **last_updated**: 260701_agenticjudge_relocate

---

## 1. 任务特征

Creative/Score/Synthesis/Multimodal 类任务，交付物含 SVG/HTML/乐谱/图表文件。

---

## 2. 核心原则

必检项中至少 1 条须做**数值级或执行级**核对：从 workspace 输入读期望数值/规格，与产物解析结果做容差对照；或对产物做可重复执行检查（解析 DOM/路径数据并核对关键度量）。只做"文件存在 + 元素计数 + 文本锚点"这类表面结构检查的信号，命中上限只有 0.5，不能组合多个表面检查等效替代深度核对。

审美/布局类的主观判断（"这个图表好不好看"）走 agentic_judge（见本 domain 的 `agentic_judge_dimensions`），不要硬套成关键词检查。

---

## 3. 代码示例

```python
def _deep_numeric_check(workspace_path):
    """
    1.0 - 从 SVG/HTML 解析出的关键度量（坐标、数值标签）与 workspace 输入规格容差内一致
    0.5 - 元素结构存在但数值有偏差
    0.0 - 元素缺失或数值严重偏离
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
    仅统计元素个数/标签名/文本锚点——单独存在时上限 0.5，
    必须与 _deep_numeric_check 组合，不能替代它。
    """
    ...
```

agentic_judge 部分（布局/审美维度）参照 `creative/narrative-quality.md` 的写法，把 `judge_question` 换成"这份可视化的布局是否清晰、达成了展示目的"，schema 与调用方式一致。

---

## 4. 迭代记录

| 版本 | 实验 | 改动摘要 |
|---|---|---|
| v1 | 260625 | 首次发现表面结构检查代替深度核对的问题 |
| v2 | 260701_agenticjudge | 从统一规则文档下放为独立 domain guide，补充 agentic_judge 维度 |
