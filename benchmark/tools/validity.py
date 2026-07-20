"""benchmark 有效性自检 V1–V4。只读 benchmark（V1/V3 临时 stage 含-gt workspace）。"""
from __future__ import annotations
import json
import tempfile
import traceback
from pathlib import Path

from benchmark.tools import lib, paths


# 注：exec 无 timeout；这些是 benchmark 自带的可信官方 grader 源（一次性 validity pass）
def _run_official_grader(grader_src: str, ws_path: Path) -> dict:
    try:
        ns: dict = {"__name__": "official_run"}
        exec(compile(grader_src, "official_grader", "exec"), ns)
        if "grade" not in ns:
            return {"_error": "no grade()"}
        try:
            r = ns["grade"]([], str(ws_path))
        except TypeError:
            r = ns["grade"](str(ws_path))
        return r if isinstance(r, dict) else {"_error": "non-dict"}
    except Exception:
        return {"_error": traceback.format_exc(limit=3)}


def _passed_from_score(d: dict, thr: float = 0.99) -> bool | None:
    if "_error" in d:
        return None
    # 0.99 阈值容浮点误差：官方 grader 的 overall_score 多是精确分数（如 4/4=1.0）
    for k in ("overall_score", "score", "total_score"):
        if isinstance(d.get(k), (int, float)):
            return float(d[k]) >= thr
    if isinstance(d.get("passed"), bool):
        return d["passed"]
    return None


def run(bench_root: Path) -> dict:
    tasks_dir = bench_root / "tasks"
    task_dirs = sorted(p for p in tasks_dir.iterdir() if p.is_dir()) if tasks_dir.exists() else []

    v1 = {"checked": 0, "inconsistent": []}
    v2 = {"per_task": {}, "low_discrimination": []}
    # V3：静态记录哪些 task 的官方 grader 读 gt——这些是需要人工核对 gold 参考解的子集。
    # 注：真正"跑 gt 参考解确认 pass"的执行式 sanity 是 future work（仅 calendar/sam3 有 gt）。
    v3 = {"grader_reads_gt_count": 0, "tasks_reading_gt": []}
    v4 = {"per_task": {}, "low_reachable": []}

    for td in task_dirs:
        tid = td.name
        gv = td / "gold_verifier"
        labels = json.loads((gv / "labels.json").read_text())
        grader_src = (gv / "official_grader.py").read_text()
        cand_passed = {k: v.get("passed") for k, v in labels["candidates"].items()}

        # V2 区分度
        passes = [p for p in cand_passed.values() if p is not None]
        n_pass = sum(1 for p in passes if p)
        v2["per_task"][tid] = {"n": len(passes), "n_pass": n_pass}
        if passes and (n_pass == 0 or n_pass == len(passes)):
            v2["low_discrimination"].append(tid)

        # V4 可达权重
        reach = json.loads((gv / "reachability.json").read_text())
        rw = reach.get("reachable_weight", 1.0)
        v4["per_task"][tid] = rw
        if rw < 0.4:
            v4["low_reachable"].append(tid)

        # V1 gold 自洽：含-gt workspace 重跑官方 grader
        for key in labels["candidates"]:
            with tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp) / "ws"
                if not lib.build_one_workspace(tid, key, ws, keep_gt=True):
                    continue
                got = _passed_from_score(_run_official_grader(grader_src, ws))
                v1["checked"] += 1
                gold = cand_passed.get(key)
                if got is not None and gold is not None and got != gold:
                    v1["inconsistent"].append({"task": tid, "candidate": key,
                                               "rerun": got, "gold": gold})

        # V3：记录读 gt 的 task（待人工核 gold 参考解）
        if reach.get("grader_reads_gt"):
            v3["grader_reads_gt_count"] += 1
            v3["tasks_reading_gt"].append(tid)

    report = {"v1_gold_consistency": v1, "v2_discrimination": v2,
              "v3_gt_sanity": v3, "v4_reachable_weight": v4}

    rd = bench_root / "_stage"; rd.mkdir(exist_ok=True)
    lines = ["# Benchmark 有效性自检", "",
             f"## V1 gold 自洽：重跑 {v1['checked']} 个，{len(v1['inconsistent'])} 个不一致",
             *[f"- {x['task']}/{x['candidate']}: 重跑={x['rerun']} gold={x['gold']}" for x in v1["inconsistent"][:30]],
             "", f"## V2 区分度：{len(v2['low_discrimination'])} 个低区分度 task",
             *[f"- {t}" for t in v2["low_discrimination"][:30]],
             "", f"## V3 读 gt 的 task：{v3['grader_reads_gt_count']} 个（需人工核 gold 参考解）",
             *[f"- {t}" for t in v3["tasks_reading_gt"][:30]],
             "", f"## V4 可达权重：{len(v4['low_reachable'])} 个 < 0.4",
             *[f"- {t}: {v4['per_task'][t]}" for t in v4["low_reachable"][:30]]]
    (rd / "validity_report.md").write_text("\n".join(lines))
    return report


if __name__ == "__main__":
    import sys
    r = run(Path(sys.argv[1]) if len(sys.argv) > 1 else paths.BENCH_OUT)
    _summary_key = {"v1_gold_consistency": "inconsistent", "v2_discrimination": "low_discrimination",
                    "v3_gt_sanity": "tasks_reading_gt", "v4_reachable_weight": "low_reachable"}
    print(json.dumps({k: len(r[k].get(_summary_key[k], [])) for k in r}, ensure_ascii=False))
