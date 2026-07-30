"""多维一致性指标（纯函数）。obs = (task,candidate) 观测列表。"""
from __future__ import annotations
import itertools
from collections import defaultdict


def _comparable(obs: list[dict]) -> list[dict]:
    """derived/gold passed 都非 None 的观测。"""
    return [o for o in obs if o["derived_passed"] is not None and o["gold_passed"] is not None]


def d1_outcome(obs: list[dict]) -> dict:
    cmp = _comparable(obs)
    n = len(cmp)
    agree = sum(1 for o in cmp if o["derived_passed"] == o["gold_passed"])
    micro = agree / n if n else None
    by_task = defaultdict(list)
    for o in cmp:
        by_task[o["task_id"]].append(o["derived_passed"] == o["gold_passed"])
    task_acc = [sum(v) / len(v) for v in by_task.values()]
    macro = sum(task_acc) / len(task_acc) if task_acc else None
    return {"micro": micro, "macro": macro, "n": n, "agree": agree, "n_tasks": len(by_task)}


def d1_prime(obs: list[dict]) -> dict:
    cmp = _comparable(obs)
    fp = sum(1 for o in cmp if o["derived_passed"] is True and o["gold_passed"] is False)
    ff = sum(1 for o in cmp if o["derived_passed"] is False and o["gold_passed"] is True)
    return {"false_pass": fp, "false_fail": ff, "n": len(cmp)}


def _rank(xs: list[float]) -> list[float]:
    """平均秩（处理并列）。"""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        # 找到与 xs[order[i]] 相等的一段连续值（处理并列）
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0           # 1-based 平均秩
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(a: list[float], b: list[float]) -> float | None:
    n = len(a)
    if n < 2:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((x - mb) ** 2 for x in b)
    if va == 0 or vb == 0:
        return None
    return cov / (va ** 0.5 * vb ** 0.5)


def d2_score(obs: list[dict]) -> dict:
    # score 可能为 None 即使 passed 非 None，所以按数值独立过滤（不复用 _comparable）
    pairs = [(o["derived_score"], o["gold_score"]) for o in obs
             if isinstance(o["derived_score"], (int, float)) and isinstance(o["gold_score"], (int, float))]
    if not pairs:
        return {"mae": None, "spearman": None, "n": 0}
    mae = sum(abs(d - g) for d, g in pairs) / len(pairs)
    d_list = [p[0] for p in pairs]
    g_list = [p[1] for p in pairs]
    spearman = _pearson(_rank(d_list), _rank(g_list))
    return {"mae": mae, "spearman": spearman, "n": len(pairs)}


def _sign(x: float) -> int:
    return (x > 0) - (x < 0)


def d3_rank(obs: list[dict]) -> dict:
    """每 task 内 candidates 的成对排序一致（判别力）。

    kendall_tau = (concordant - discordant) / n_pairs。n_pairs 排除 gold 并列对
    （并列无判别信号），但包含 derived 并列对（gold 非并列却 derived 并列 → 记 neither，
    计入分母作惩罚）。这既非 tau-a 也非 tau-b，是"系统排序 vs 含并列参考"的常用约定。
    """
    by_task = defaultdict(list)
    for o in obs:
        if isinstance(o["derived_score"], (int, float)) and isinstance(o["gold_score"], (int, float)):
            by_task[o["task_id"]].append(o)
    concordant = discordant = n_pairs = 0
    for items in by_task.values():
        for x, y in itertools.combinations(items, 2):
            gs = _sign(x["gold_score"] - y["gold_score"])
            if gs == 0:
                continue                    # gold 并列，不计入判别力
            ds = _sign(x["derived_score"] - y["derived_score"])
            n_pairs += 1
            if ds == gs:
                concordant += 1
            elif ds == -gs:
                discordant += 1
            # ds==0（derived 并列）算 neither：既不一致也不反序
    pairwise_acc = concordant / n_pairs if n_pairs else None
    kendall = (concordant - discordant) / n_pairs if n_pairs else None
    return {"pairwise_acc": pairwise_acc, "kendall_tau": kendall, "n_pairs": n_pairs}


def d1_score_threshold(obs: list[dict], threshold: float = 0.99) -> dict:
    """D1 对照口径：derived_passed vs (gold_score >= threshold)。

    与主口径（vs gold_passed）对照：对照 micro 高于主口径 → 分歧多是"阈值效应"
    （gold passed 阈值很严，接近满分仍判 fail）；对照不高于主口径 → verifier 真不一致。
    """
    rows = [o for o in obs if o["derived_passed"] is not None
            and isinstance(o["gold_score"], (int, float))]
    n = len(rows)
    def _gold_bin(o):
        return o["gold_score"] >= threshold
    agree = sum(1 for o in rows if o["derived_passed"] == _gold_bin(o))
    micro = agree / n if n else None
    by_task = defaultdict(list)
    for o in rows:
        by_task[o["task_id"]].append(o["derived_passed"] == _gold_bin(o))
    task_acc = [sum(v) / len(v) for v in by_task.values()]
    macro = sum(task_acc) / len(task_acc) if task_acc else None
    return {"micro": micro, "macro": macro, "n": n, "threshold": threshold}


def per_task_agreement(obs: list[dict]) -> dict:
    """逐 task 聚合 derived vs gold 的 outcome 可比一致数（通用评测视图）。

    只计 derived/gold passed 均非 None 的观测。返回
    {task_id: {"n": int, "agree": int, "cands": [{"cand","derived","gold"}]}}。
    供实验侧 audit_input / progression_matrix 等共用，避免各自重算。
    """
    by_task: dict = {}
    for o in _comparable(obs):
        t = by_task.setdefault(o["task_id"], {"n": 0, "agree": 0, "cands": []})
        t["n"] += 1
        t["agree"] += int(o["derived_passed"] == o["gold_passed"])
        t["cands"].append({"cand": o.get("cand"),
                           "derived": o["derived_passed"], "gold": o["gold_passed"]})
    return by_task


def reachable_weighted_macro(obs: list[dict], reachable_weight: dict[str, float]) -> dict:
    """每 task 的 outcome 一致率，按 reachable_weight 加权平均；同时返回 raw（等权）macro 作对照。

    缺席于 reachable_weight 的 task 默认权重 1.0（等权回退）。注意：若权重 dict 意外为空或
    task id 写错，weighted 会静默等于 raw——调用方应在上游校验权重 dict。
    """
    cmp = _comparable(obs)
    by_task = defaultdict(list)
    for o in cmp:
        by_task[o["task_id"]].append(o["derived_passed"] == o["gold_passed"])
    task_acc = {t: sum(v) / len(v) for t, v in by_task.items()}
    if not task_acc:
        return {"raw_macro": None, "reachable_weighted_macro": None}
    raw = sum(task_acc.values()) / len(task_acc)
    num = sum(task_acc[t] * reachable_weight.get(t, 1.0) for t in task_acc)
    den = sum(reachable_weight.get(t, 1.0) for t in task_acc)
    rwm = num / den if den > 0 else None
    return {"raw_macro": raw, "reachable_weighted_macro": rwm}
