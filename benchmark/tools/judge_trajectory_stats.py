# benchmark/tools/judge_trajectory_stats.py
"""实验后一次性扫描 agentic_judge 落盘的轨迹文件，统计调用情况——不是实时账本。

不依赖 grader.py 自己上报任何数字：judge_harness.py（技能自带、非 LLM 现写、
可信）在每次真的发起子进程调用时会把完整轨迹落盘到 VERIFIER_JUDGE_LOG_DIR
（见 judge_harness._persist_trajectory），本工具只做物理事实层面的统计——
"这棵目录树下真的有多少个轨迹文件"，比信任被评测对象的自我报告更贴近 C24
"基于事实行为而非易误报启发式"的精神。

目录结构由调用方约定（本 bench 用 {log_root}/{task_id}/{cand_key}/*.jsonl），
本工具不关心具体分层含义，只统计"文件"与"文件所在的直接父目录"这两个物理事实。
"""
from __future__ import annotations
import json
from pathlib import Path

from benchmark.tools import leak_scan


def scan(log_root: Path) -> dict:
    log_root = Path(log_root)
    if not log_root.exists():
        return {
            "total_files": 0, "total_observations_with_judge": 0,
            "total_bytes": 0, "leak_hits": 0, "per_dir_sample_counts": {},
        }
    files = sorted(log_root.rglob("*.jsonl"))
    per_dir: dict[str, int] = {}
    total_bytes = 0
    leak_hits = 0
    for f in files:
        rel_dir = str(f.parent.relative_to(log_root))
        per_dir[rel_dir] = per_dir.get(rel_dir, 0) + 1
        total_bytes += f.stat().st_size
        text = f.read_text(encoding="utf-8", errors="replace")
        events = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        leak_hits += len(leak_scan.scan_trajectory(events))
    return {
        "total_files": len(files),
        "total_observations_with_judge": len(per_dir),
        "total_bytes": total_bytes,
        "leak_hits": leak_hits,
        "per_dir_sample_counts": per_dir,
    }


def render(stats: dict) -> str:
    lines = [
        "# Agentic-Judge 轨迹统计（实验后一次性扫描，非实时账本）", "",
        f"触发过 agentic_judge 的观测数：**{stats['total_observations_with_judge']}**",
        f"总采样文件数：**{stats['total_files']}**",
        f"总轨迹字节数：**{stats['total_bytes']}**",
        f"反泄漏复核命中：**{stats['leak_hits']}**（应为 0；非 0 需人工打开对应轨迹文件复核）",
        "",
    ]
    return "\n".join(lines) + "\n"


def main():
    import argparse
    ap = argparse.ArgumentParser(description="扫 VERIFIER_JUDGE_LOG_DIR 目录树，统计 agentic_judge 调用情况（实验后一次性用）")
    ap.add_argument("log_root", type=Path)
    ap.add_argument("--out", type=Path, default=None, help="把原始统计 dict 存成 json")
    a = ap.parse_args()
    stats = scan(a.log_root)
    print(render(stats))
    if a.out:
        a.out.write_text(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
