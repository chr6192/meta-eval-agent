> Language: **English** · [中文](narrative-quality.zh-CN.md)

# Domain Verifier Reference Guide: creative/narrative-quality

> **domain_id**: `creative/narrative-quality`
> **category**: Creative
> **gate_policy**: strict-if-checkable
> **layer_hint**: mostly-agentic-judge
> **last_updated**: 260701_agenticjudge_seed

---

## 1. Task characteristics

The task requires producing narrative text: risk-attribution explanations, financial-anomaly explanations, creative copy, meeting-minutes summaries, and the like. The core quality dimension for this class of task is **semantic coherence and argumentative sufficiency** — not "whether certain structural markers appear."

**Typical signal**: the prompt contains words like "write," "explain," "explain why," "attribute," and there is no fixed structured-output schema (JSON/CSV).

---

## 2. Why this domain mostly routes to agentic_judge

If the grader implements dimensions like "does the argument hold up" or "is the narrative coherent" as "check whether N relevant keywords appear," it is essentially approximating semantic quality with keyword density — a text that is a patchwork of keywords but has no logic can fool a keyword check, while a text that uses synonyms or different sentence structures but has a solid argument may be misjudged simply for not hitting enough keywords. **This is exactly the kind of scenario that needs agentic_judge**: the agent can actually read the meaning and judge "does this argument hold up," rather than counting keywords.

---

## 3. How to write the Deterministic layer (this domain is not entirely without one)

Even when the quality dimensions are delegated to agentic_judge, the Deterministic layer should still retain **existence anchors** (not subjective judgment — hard factual checks):

```python
def _deliverable_present(workspace_path):
    """
    1.0 - the deliverable file exists and is non-empty (>50 characters)
    0.0 - missing or empty file
    """
    path = _find_deliverable(workspace_path)
    if path is None:
        return 0.0
    text = path.read_text(errors="replace").strip()
    return 1.0 if len(text) > 50 else 0.0


def _required_datapoint_cited(workspace_path, required_value):
    """
    If the prompt explicitly requires citing a specific data point (e.g., an amount/date
    from the fixture), check whether it appears verbatim in the deliverable — this is an
    existence anchor, not a semantic judgment, and still belongs to the Deterministic layer.
    1.0 - the data point appears verbatim; 0.0 - it does not appear
    """
    text = _read_deliverable_text(workspace_path)
    return 1.0 if required_value in text else 0.0
```

---

## 4. How to write the agentic_judge layer

```python
from judge_harness import invoke_agentic_judge

JUDGE_PROMPT = (
    "Evaluate the candidate deliverable (locate the primary .md/.txt report file). "
    "For each dimension, give a score of 0.0-1.0 and cite specific passages as evidence; "
    "if no evidence can be found, score that dimension 0 and note no_evidence."
)
JUDGE_SCHEMA = {
    "dimensions": {
        "narrative_coherence": {"description": "Whether the narrative develops around the topic, is logically coherent, and has no internal contradictions"},
        "evidence_grounded_not_keyword_stuffed": {"description": "Whether key claims are backed by concrete data/facts, rather than keyword stuffing"},
    }
}

def _agentic_judge_signals(workspace_path):
    result = invoke_agentic_judge(JUDGE_PROMPT, JUDGE_SCHEMA, workspace_path=workspace_path, k=3)
    if not result["available"]:
        return {"narrative_coherence": 0.0, "evidence_grounded_not_keyword_stuffed": 0.0}
    return {k: v["score"] for k, v in result["dimensions"].items()}
```

**Note**: by default these two dimensions count only as bonus signals, not as must-pass criteria. Unless the entire task is confirmed to have absolutely no Deterministic-layer anchor at all (not even "does the deliverable exist" — an extremely rare case), the PASS/FAIL gate is still decided by the Deterministic layer.

---

## 5. Known Pitfalls

- **Pitfall 1**: implementing "whether the argument is factually grounded" as a keyword check again (e.g., "does it contain 3+ financial terms") — this is disguising a Deterministic-layer technique as agentic_judge; it must actually go through `invoke_agentic_judge`.
- **Pitfall 2**: letting agentic_judge's core intent judgment directly determine `outcome_passed` without first confirming that the whole task truly has no Deterministic anchor at all.

---

## 6. Change Log

| Version | Experiment | Summary of changes |
|---|---|---|
| v1 | 260701_agenticjudge seed | Initial creation |
