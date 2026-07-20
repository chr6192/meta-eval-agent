"""benchmark 正确性自检：隔离 / schema / gold 可跑 / 抽样。只读，不改 benchmark。"""
from __future__ import annotations
import json
from pathlib import Path

from benchmark.tools import lib

REQUIRED_AI = ["task_md.md"]
REQUIRED_GV = ["labels.json", "official_grader.py", "official_rubric.md", "reachability.json"]
SCORING_HEADERS = ["## Automated Checks", "## Grading Criteria", "## LLM Judge Rubric", "## Expected Behavior"]


def run(bench_root: Path) -> dict:
    failures: list[str] = []
    tasks_dir = bench_root / "tasks"
    task_dirs = sorted(p for p in tasks_dir.iterdir() if p.is_dir()) if tasks_dir.exists() else []

    for td in task_dirs:
        tid = td.name
        ai, gv = td / "verifier_author_inputs", td / "gold_verifier"
        # ① 隔离：无 GT 路径、task_md 无评分侧段
        for p in ai.rglob("*"):
            if p.is_file() and lib.is_gt_path(p.relative_to(ai)):
                failures.append(f"{tid}: author 输入层含 GT 文件 {p.relative_to(ai)}")
        md = (ai / "task_md.md")
        if md.exists():
            txt = md.read_text()
            for h in SCORING_HEADERS:
                if h in txt:
                    failures.append(f"{tid}: task_md 残留评分侧段 {h}")
            for item in lib.parse_workspace_files(txt):
                for v in (item.get("source", ""), item.get("dest", "")):
                    if v and lib.is_gt_path(Path(v)):
                        failures.append(f"{tid}: task_md workspace_files 残留 GT 路径 {v}（C3/C17 泄漏）")
        # ② schema
        for f in REQUIRED_AI:
            if not (ai / f).exists():
                failures.append(f"{tid}: 缺 {f}")
        for f in REQUIRED_GV:
            if not (gv / f).exists():
                failures.append(f"{tid}: 缺 gold_verifier/{f}")
        # gold 的 JSON 必须可解析（截断/损坏的写入靠存在性查不出）
        for jf in ("labels.json", "reachability.json"):
            jp = gv / jf
            if jp.exists():
                try:
                    json.loads(jp.read_text())
                except (json.JSONDecodeError, ValueError) as e:
                    failures.append(f"{tid}: gold_verifier/{jf} 不是合法 JSON ({e})")
        # candidate 完整性
        for cdir in (ai / "candidates").iterdir() if (ai / "candidates").exists() else []:
            if not cdir.is_dir():
                continue   # 跳过 .DS_Store 等杂散文件，避免误报
            if not (cdir / "workspace").is_dir():
                failures.append(f"{tid}/{cdir.name}: 缺 workspace")
            if not (cdir / "transcript.jsonl").exists():
                failures.append(f"{tid}/{cdir.name}: 缺 transcript.jsonl")
        # ③ gold 可 import
        gp = gv / "official_grader.py"
        if gp.exists():
            try:
                compile(gp.read_text(), str(gp), "exec")
            except SyntaxError as e:
                failures.append(f"{tid}: official_grader 编译失败 {e}")

    report_dir = bench_root / "_stage"
    report_dir.mkdir(exist_ok=True)
    lines = ["# Benchmark 正确性自检", "",
             f"- 检查 task 数: {len(task_dirs)}",
             f"- 失败项: {len(failures)}", ""]
    lines += [f"- ❌ {f}" for f in failures] or ["- ✅ 全部通过"]
    (report_dir / "self_test_report.md").write_text("\n".join(lines))
    return {"passed": not failures, "failures": failures, "n_tasks": len(task_dirs)}


if __name__ == "__main__":
    import sys
    from benchmark.tools import paths
    r = run(Path(sys.argv[1]) if len(sys.argv) > 1 else paths.BENCH_OUT)
    print("PASS" if r["passed"] else f"FAIL: {len(r['failures'])} 项")
    raise SystemExit(0 if r["passed"] else 1)
