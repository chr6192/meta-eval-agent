"""静态解析官方 grader → 每个评分维度的可达性。拿不准标 needs_manual。

`analyze()` 支持 `agentic_judge_capable` 参数：默认关闭时 llm-judgment 维度按历史假设
（generated grader 只能是纯确定性代码）视为恒不可达；显式开启时才承认 grader 具备
agentic_judge（子进程调用本地 agent CLI 做语义裁决）能力，从而让该维度计入可达权重。
"""
from __future__ import annotations
import ast
import re

# 用 token 集匹配（criterion 是 snake_case）；避免子串误伤，如 "ratio" 命中 "duration"
_ORACLE_TOKENS = {"optimal", "optimality", "iou", "gt", "groundtruth", "oracle", "expected", "reference"}
_TRANSCRIPT_TOKENS = {"step", "steps", "trajectory", "process", "tool", "reason", "reasoning"}
_GT_READ_HINT = re.compile(r"(?i)gt/|optimal_|expected_|reference_|ground[_.]?truth|/gt\b")


def _name_tokens(name: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", name.lower()) if t}


def _classify_criterion(name: str, grader_reads_gt: bool) -> tuple[str, bool]:
    toks = _name_tokens(name)
    if grader_reads_gt and (toks & _ORACLE_TOKENS):
        return "oracle", False     # 需 gt 参考解对比，generated grader 够不着
    if toks & _TRANSCRIPT_TOKENS:
        return "transcript", True
    return "workspace", True


def _extract_criteria(grader_src: str) -> tuple[list[str], str]:
    """优先 ALL_CRITERIA=[...]；否则收集 snake_case 字面量作为黑盒兜底。返回(criteria, method)。"""
    crits: list[str] = []
    method = "none"
    if not grader_src:
        return crits, method
    try:
        tree = ast.parse(grader_src)
    except SyntaxError:
        tree = None
    if tree:
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id in ("ALL_CRITERIA", "CRITERIA"):
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            crits = [e.value for e in node.value.elts
                                     if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                            method = "all_criteria"
    if not crits and method != "all_criteria":
        # 退化：收集字符串字面量里像 criterion 名的（snake_case 单词）
        seen = []
        for m in re.finditer(r'["\']([a-z][a-z0-9_]{3,40})["\']', grader_src):
            w = m.group(1)
            if w not in seen and "_" in w:
                seen.append(w)
        crits = seen
        if crits:
            method = "fallback"
    # 去掉聚合名
    filtered = [c for c in crits if c not in ("overall_score", "score", "total_score")]
    return filtered, method


def _llm_judge_weight(task_md_text: str) -> float:
    m = re.search(r"grading_weights:\s*\n(.*?)(?=\n[a-zA-Z_]+:|\n---|\Z)", task_md_text, re.S)
    if not m:
        return 0.0
    lm = re.search(r"llm_judge:\s*([0-9.]+)", m.group(1))
    return float(lm.group(1)) if lm else 0.0


def analyze(task_id: str, grader_src: str, task_md_text: str,
            agentic_judge_capable: bool = False) -> dict:
    """`agentic_judge_capable` 参数化"llm-judgment 是否物理可达"这一假设：默认 False
    保持历史行为（generated grader 视为纯确定性代码，llm-judgment 恒不可达，向后兼容旧实验
    的 reachability 解读）；仅当调用方显式声明 grader 具备 agentic_judge 能力（可调用本地
    agent CLI 做语义裁决的子进程能力）时才传 True，此时 __llm_judge_overall__ 才标记为可达。
    """
    criteria, extraction_method = _extract_criteria(grader_src)
    grader_reads_gt = bool(_GT_READ_HINT.search(grader_src or ""))
    llm_w = _llm_judge_weight(task_md_text)

    dims = []
    oracle_count = 0
    for c in criteria:
        dep, reach = _classify_criterion(c, grader_reads_gt)
        if dep == "oracle":
            oracle_count += 1
        dims.append({"criterion": c, "depends_on": dep, "reachable": reach})

    # llm-judgment 作为 task 级附加维度（criterion 难逐条映射）
    if llm_w > 0:
        dims.append({"criterion": "__llm_judge_overall__",
                     "depends_on": "llm-judgment", "reachable": agentic_judge_capable})

    n = max(len(criteria), 1)
    oracle_frac = oracle_count / n
    if agentic_judge_capable:
        reachable_weight = max(0.0, min(1.0, 1.0 - oracle_frac))
    else:
        reachable_weight = max(0.0, min(1.0, (1.0 - llm_w) * (1.0 - oracle_frac)))

    needs_manual = (not criteria) or (extraction_method == "fallback") or (grader_reads_gt and oracle_count == 0)
    return {
        "task_id": task_id,
        "dimensions": dims,
        "reachable_weight": round(reachable_weight, 3),
        "llm_judge_weight": llm_w,
        "grader_reads_gt": grader_reads_gt,
        "needs_manual": needs_manual,
        "extraction_method": extraction_method,
    }
