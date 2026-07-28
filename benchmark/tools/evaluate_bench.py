"""编排：produced graders × benchmark → 多维指标 + 报告。CLI。"""
from __future__ import annotations
import json
import os
from pathlib import Path

from benchmark.tools import bench_load, run_grader, metrics, paths


def evaluate(bench_root: Path, produced_root: Path, split: str, report_dir: Path | None = None) -> dict:
    obs = []
    task_ids = list(bench_load.iter_split_tasks(bench_root, split))
    for tid in task_ids:
        gold = bench_load.load_task_gold(bench_root, tid)
        grader = produced_root / tid / "grader.py"
        for cand, gl in gold.labels["candidates"].items():
            io = bench_load.load_candidate_io(bench_root, tid, cand)
            if grader.exists():
                if report_dir:
                    os.environ["VERIFIER_JUDGE_LOG_DIR"] = str(
                        Path(report_dir) / "_judge_trajectories" / tid / cand)
                r = run_grader.run(grader, io.transcript, io.workspace_path)
            else:
                r = {"outcome_passed": None, "score": None, "criteria": [], "_error": "no produced grader"}
            obs.append({
                "task_id": tid, "cand": cand,
                "derived_passed": r["outcome_passed"], "gold_passed": gl["passed"],
                "derived_score": r["score"], "gold_score": gl.get("score"),
            })

    rw = {tid: bench_load.load_task_gold(bench_root, tid).reachable_weight for tid in task_ids}
    d1 = metrics.d1_outcome(obs)
    report = {
        "split": split, "n_obs": len(obs),
        "n_tasks": len(task_ids),
        "d1": d1,
        "d1_prime": metrics.d1_prime(obs),
        "d1_score_threshold": metrics.d1_score_threshold(obs),
        "d2": metrics.d2_score(obs),
        "d3": metrics.d3_rank(obs),
        "reachability": metrics.reachable_weighted_macro(obs, rw),
        "coverage": {
            "comparable_obs": d1["n"],
            "n_obs": len(obs),
            "comparable_rate": (d1["n"] / len(obs)) if obs else None,
            "comparable_tasks": d1["n_tasks"],
            "total_tasks": len(task_ids),
        },
    }
    if report_dir:
        report_dir = Path(report_dir); report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "eval_per_obs.jsonl").write_text(
            "".join(json.dumps(o, ensure_ascii=False) + "\n" for o in obs))
        (report_dir / "eval_report.md").write_text(_render(report))
    return report


def _render(r: dict) -> str:
    def _f(v):
        return "N/A" if v is None else v
    d1, d2, d3 = r["d1"], r["d2"], r["d3"]
    cov = r["coverage"]
    return "\n".join([
        f"# Evaluator 报告（split={r['split']}）", "",
        f"- **覆盖率 coverage**: 可比 obs {cov['comparable_obs']}/{cov['n_obs']}"
        f"（{_f(cov['comparable_rate'])}）；覆盖 task {cov['comparable_tasks']}/{cov['total_tasks']}"
        + ("  ⚠️ 低覆盖：headline 指标仅基于可比子集，谨慎解读" if (cov['comparable_rate'] or 0) < 0.5 else ""),
        f"- 观测数 n_obs: {r['n_obs']}（可比 {d1['n']}）",
        f"- **D1 outcome**: micro={_f(d1['micro'])} macro={_f(d1['macro'])}",
        f"- **D1 对照（gold score≥{r['d1_score_threshold']['threshold']}）**: "
        f"micro={_f(r['d1_score_threshold']['micro'])}（高于主口径=阈值效应；≤主口径=verifier 真错）",
        f"- **D1′ 误判**: false-pass={r['d1_prime']['false_pass']} false-fail={r['d1_prime']['false_fail']}",
        f"- **D2 score**: MAE={_f(d2['mae'])} Spearman={_f(d2['spearman'])}",
        f"- **D3 排序**: pairwise={_f(d3['pairwise_acc'])} Kendall={_f(d3['kendall_tau'])}（{d3['n_pairs']} 对）",
        f"- **可达性归一**: raw_macro={_f(r['reachability']['raw_macro'])} "
        f"reachable_weighted={_f(r['reachability']['reachable_weighted_macro'])}",
    ])


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench-root", default=str(paths.BENCH_OUT))
    ap.add_argument("--produced-root", required=True, help="目录：<task_id>/grader.py")
    ap.add_argument("--split", default="train",
                    help="split 名，对应 <bench-root>/splits/<split>.json（默认 train/test，可自定义如 demo）")
    ap.add_argument("--report-dir", default=None)
    args = ap.parse_args()
    rep = evaluate(Path(args.bench_root), Path(args.produced_root), args.split,
                   Path(args.report_dir) if args.report_dir else None)
    print(_render(rep))


if __name__ == "__main__":
    main()
