# Domain Verifier 参考指南：creative/narrative-quality

> **domain_id**: `creative/narrative-quality`
> **category**: Creative
> **gate_policy**: strict-if-checkable
> **layer_hint**: mostly-agentic-judge
> **last_updated**: 260701_agenticjudge_seed

---

## 1. 任务特征

任务要求产出叙述性文本：风险归因说明、财务异常解释、创作文案、会议纪要摘要等。这类任务的核心质量维度是**语义连贯性与论证充分性**，不是"是否出现某些结构标记"。

**典型信号**：Prompt 含"撰写"、"说明"、"解释为什么"、"归因"等词，且没有固定的结构化输出 schema（JSON/CSV）。

---

## 2. 为什么这个 domain 主要走 agentic_judge

如果 grader 对"论证是否成立""叙述是否连贯"这类维度写"检查是否出现 N 个相关关键词"，本质上是在用关键词密度近似语义质量——一份东拼西凑关键词但毫无逻辑的文本能骗过关键词检查，一份用同义词/不同句式表达但论证扎实的文本可能因为关键词命中数不够被误判。**这正是需要 agentic_judge 的场景**：agent 能读懂语义、能判断"这段论证是否成立"，而不是数关键词。

---

## 3. Deterministic 层怎么写（这个 domain 也不是完全没有 Deterministic 层）

即使质量维度交给 agentic_judge，仍应保留 Deterministic 层的**存在性锚点**（不是主观判断，是硬事实检查）：

```python
def _deliverable_present(workspace_path):
    """
    1.0 - 交付物文件存在且非空（>50 字符）
    0.0 - 缺失或空文件
    """
    path = _find_deliverable(workspace_path)
    if path is None:
        return 0.0
    text = path.read_text(errors="replace").strip()
    return 1.0 if len(text) > 50 else 0.0


def _required_datapoint_cited(workspace_path, required_value):
    """
    若 Prompt 明确要求引用某个具体数据点（如 fixture 里的金额/日期），
    检查它是否原样出现在产物里——这是存在性锚点，不是语义判断，仍属 Deterministic 层。
    1.0 - 数据点原文出现；0.0 - 未出现
    """
    text = _read_deliverable_text(workspace_path)
    return 1.0 if required_value in text else 0.0
```

---

## 4. agentic_judge 层怎么写

```python
from judge_harness import invoke_agentic_judge

JUDGE_PROMPT = (
    "评估候选交付物（找到主要的 .md/.txt 报告文件）。"
    "对每个维度给 0.0-1.0 分并引用具体段落作为证据；找不到证据时该维度给 0 分并注明 no_evidence。"
)
JUDGE_SCHEMA = {
    "dimensions": {
        "narrative_coherence": {"description": "叙述是否围绕主题展开、逻辑连贯、无前后矛盾"},
        "evidence_grounded_not_keyword_stuffed": {"description": "关键论断是否有具体数据/事实支撑，而非关键词堆砌"},
    }
}

def _agentic_judge_signals(workspace_path):
    result = invoke_agentic_judge(JUDGE_PROMPT, JUDGE_SCHEMA, workspace_path=workspace_path, k=3)
    if not result["available"]:
        return {"narrative_coherence": 0.0, "evidence_grounded_not_keyword_stuffed": 0.0}
    return {k: v["score"] for k, v in result["dimensions"].items()}
```

**注意**：这两个维度默认只进加分项，不进必检项。除非整个任务确认完全没有 Deterministic 层锚点（连"交付物是否存在"都不算——这种情况极罕见），否则 PASS/FAIL 闸门仍由 Deterministic 层决定。

---

## 5. 已知陷阱

- **陷阱 1**：把"论证是否有事实支撑"又实现成关键词检查（比如"是否出现 3 个以上财务术语"）——这就是在用 Deterministic 层的手法冒充 agentic_judge，必须真的走 `invoke_agentic_judge`。
- **陷阱 2**：让 agentic_judge 的核心意图判断直接决定 `outcome_passed`，而没有先确认整个任务真的无任何 Deterministic 锚点。

---

## 6. 迭代记录

| 版本 | 实验 | 改动摘要 |
|---|---|---|
| v1 | 260701_agenticjudge seed | 初始创建 |
