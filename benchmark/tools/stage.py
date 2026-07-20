"""stage 管线：从原始数据产出 benchmark 两层目录。stage.py 是唯一写 benchmark 的地方。"""
from __future__ import annotations
import json
import re
import shutil
from pathlib import Path

from benchmark.tools import paths, lib, transcript_norm, reachability


def _stage_official_rubric(sections: dict) -> str:
    parts = []
    for key, header in [("expected_behavior", "## Expected Behavior"),
                        ("grading_criteria", "## Grading Criteria"),
                        ("llm_judge_rubric", "## LLM Judge Rubric")]:
        if sections.get(key):
            parts.append(f"{header}\n\n{sections[key]}")
    return "\n\n".join(parts) + "\n" if parts else "(无评分标准段)\n"


def stage_one_task(task_id: str, out_root: Path) -> dict:
    """产出 out_root/{task_id}/ 两层目录。返回该 task 的 manifest 条目。"""
    md = lib.resolve_task_md(task_id)
    if not md:
        return {"task_id": task_id, "status": "skipped", "reason": "no task md"}
    md_text = md.read_text()
    stripped, sections = lib.strip_task_md(md_text)
    grader_src = sections.get("automated_checks")

    root = out_root / task_id
    ai = root / "verifier_author_inputs"
    gv = root / "gold_verifier"
    if root.exists():
        shutil.rmtree(root)
    (ai / "candidates").mkdir(parents=True)
    gv.mkdir(parents=True)

    # --- author 输入层 ---
    (ai / "task_md.md").write_text(stripped)
    _stage_inputs(task_id, md_text, ai / "inputs")

    covered = []
    for spec in paths.CANDIDATE_SPECS:
        key = spec["key"]
        cdir = ai / "candidates" / key
        ok = lib.build_one_workspace(task_id, key, cdir / "workspace", keep_gt=False)
        if not ok:
            continue
        src_tr = paths.FRAMEWORK_BASES[key] / "transcripts" / f"{task_id}.jsonl"
        if src_tr.exists():
            transcript_norm.normalize_transcript(src_tr, cdir / "transcript.jsonl")
        else:
            (cdir / "transcript.jsonl").write_text("")
        covered.append(key)

    # --- gold 层 ---
    labels = {"task_id": task_id, "grading_type": _grading_type(md_text), "candidates": {}}
    # covered 里若某 candidate 无 framework 跑分结果，则该 candidate 不进 labels（degenerate 但合法）
    for key in covered:
        r = lib.framework_result(task_id, key)
        if r is None:
            continue
        labels["candidates"][key] = {
            "passed": bool(r.get("passed", False)),
            "score": r.get("score"),
            "max_score": r.get("max_score"),
            "breakdown": r.get("breakdown", {}),
            "source": "framework_results",
        }
    (gv / "labels.json").write_text(json.dumps(labels, ensure_ascii=False, indent=2))
    (gv / "official_grader.py").write_text(grader_src or "# no official grader\n")
    (gv / "official_rubric.md").write_text(_stage_official_rubric(sections))
    reach = reachability.analyze(task_id, grader_src or "", md_text)
    (gv / "reachability.json").write_text(json.dumps(reach, ensure_ascii=False, indent=2))

    return {"task_id": task_id, "status": "ok", "candidates": covered,
            "gt_isolated": True, "grading_type": labels["grading_type"]}


def _grading_type(md_text: str) -> str:
    m = re.search(r"^grading_type:\s*(\S+)", md_text, re.M)
    return m.group(1) if m else "unknown"


def _stage_inputs(task_id: str, md_text: str, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    lib.copy_baseline_files(task_id, md_text, dst, keep_gt=False)


def stage_all(task_ids: list[str], splits: dict[str, list[str]], out_root: Path) -> dict:
    out_root.mkdir(parents=True, exist_ok=True)
    tasks_dir = out_root / "tasks"
    if tasks_dir.exists():
        shutil.rmtree(tasks_dir)        # 清理上一次 stage 的残留 task 目录（split 变化时避免孤儿）
    tasks_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for tid in task_ids:
        entries.append(stage_one_task(tid, tasks_dir))
    # splits 视图
    (out_root / "splits").mkdir(exist_ok=True)
    for name, ids in splits.items():
        (out_root / "splits" / f"{name}.json").write_text(
            json.dumps({"split": name, "task_ids": ids}, ensure_ascii=False, indent=2))
    manifest = {
        "name": "verifier-author-bench-v1",
        "version": "1.0.0",
        "source_benchmark": paths.SOURCE_BENCHMARK,
        "candidate_specs": paths.CANDIDATE_SPECS,
        "n_tasks": sum(1 for e in entries if e["status"] == "ok"),
        "tasks": entries,
        "gt_isolation": {"patterns": paths.GT_PATTERNS},
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


def discover_task_ids() -> list[str]:
    """从 SRC_BENCH/tasks 的所有 task md（frontmatter id:）发现全部 task_id，按文件名排序稳定。"""
    ids = []
    for p in sorted(paths.TASKS_DIR.glob("*.md")):
        m = re.search(r"^id:\s*(\S+)", p.read_text(errors="ignore")[:600], re.M)
        if m:
            ids.append(m.group(1))
    return ids


def make_split(task_ids: list[str], test_ratio: float, seed: int) -> dict[str, list[str]]:
    """确定性 train/test 切分（视图层）。benchmark 资产本身仍 stage 全量。"""
    import random
    shuffled = list(task_ids)
    random.Random(seed).shuffle(shuffled)
    n_test = round(len(shuffled) * test_ratio)
    test_ids = sorted(shuffled[:n_test])
    train_ids = sorted(shuffled[n_test:])
    return {"train": train_ids, "test": test_ids}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    # 默认写真实 BENCH_OUT（在 .gitignore 内，无 git 风险）；测试/审查请传 --out
    ap.add_argument("--out", default=str(paths.BENCH_OUT))
    ap.add_argument("--limit", type=int, default=None,
                    help="只 stage 前这么多 task（按文件名序）")
    ap.add_argument("--test-ratio", type=float, default=0.2,
                    help="train/test 视图切分中 test 占比（默认 0.2）")
    ap.add_argument("--seed", type=int, default=42, help="切分随机种子")
    args = ap.parse_args()
    all_ids = discover_task_ids()
    if args.limit is not None:
        all_ids = all_ids[:args.limit]
    splits = make_split(all_ids, args.test_ratio, args.seed)
    m = stage_all(all_ids, splits, Path(args.out))
    print(f"[stage] 产出 {m['n_tasks']}/{len(all_ids)} 个 task "
          f"(train={len(splits['train'])} / test={len(splits['test'])}) → {args.out}")


if __name__ == "__main__":
    main()
