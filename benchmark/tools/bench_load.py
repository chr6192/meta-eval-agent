"""benchmark 只读访问器。不 import/exec 任何 grader。"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TaskGold:
    task_id: str
    labels: dict                 # gold_verifier/labels.json
    reachability: dict           # gold_verifier/reachability.json
    reachable_weight: float


@dataclass
class CandidateIO:
    workspace_path: Path
    transcript: list             # 解析后的 transcript.jsonl（每行一个 message dict）


def iter_split_tasks(bench_root: Path, split: str):
    """yield split 视图里的 task_id（只 yield 实际 staged 的）。"""
    sp = json.loads((bench_root / "splits" / f"{split}.json").read_text())
    for tid in sp["task_ids"]:
        if (bench_root / "tasks" / tid / "gold_verifier" / "labels.json").exists():
            yield tid


def load_task_gold(bench_root: Path, task_id: str) -> TaskGold:
    gv = bench_root / "tasks" / task_id / "gold_verifier"
    labels = json.loads((gv / "labels.json").read_text())
    reach = json.loads((gv / "reachability.json").read_text())
    rw = float(reach.get("reachable_weight", 1.0))
    return TaskGold(task_id=task_id, labels=labels, reachability=reach, reachable_weight=rw)


def load_candidate_io(bench_root: Path, task_id: str, cand_key: str) -> CandidateIO:
    cdir = bench_root / "tasks" / task_id / "verifier_author_inputs" / "candidates" / cand_key
    ws = cdir / "workspace"
    tr_path = cdir / "transcript.jsonl"
    transcript = []
    if tr_path.exists():
        for line in tr_path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    transcript.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return CandidateIO(workspace_path=ws, transcript=transcript)
