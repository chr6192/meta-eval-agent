import json
from benchmark.tools import stage, paths


def test_stage_one_task_layout(repo_data_present, fixture_tasks, tmp_path):
    cal = fixture_tasks["calendar"]
    stage.stage_one_task(cal, tmp_path)
    root = tmp_path / cal
    ai = root / "verifier_author_inputs"
    gv = root / "gold_verifier"
    # 两层都在
    assert (ai / "task_md.md").exists()
    assert (gv / "labels.json").exists()
    assert (gv / "official_grader.py").exists()
    assert (gv / "reachability.json").exists()
    # author 输入层不含评分标准、不含 gt
    md = (ai / "task_md.md").read_text()
    assert "## Automated Checks" not in md
    assert not any(p.name == "gt" for p in ai.rglob("*"))
    # 至少一个 candidate 目录带 workspace + transcript
    cand_dirs = list((ai / "candidates").iterdir())
    assert cand_dirs
    some = cand_dirs[0]
    assert (some / "transcript.jsonl").exists()
    # labels 的 candidate key 与 candidates 目录对得上
    labels = json.loads((gv / "labels.json").read_text())
    assert set(labels["candidates"]) <= set(paths.FRAMEWORK_BASES)
    # 每个 labels candidate 都应有对应的 candidates/ 目录
    cand_dir_names = {d.name for d in (ai / "candidates").iterdir()}
    assert set(labels["candidates"]) <= cand_dir_names


def test_grading_type_fallback():
    from benchmark.tools.stage import _grading_type
    assert _grading_type("---\ngrading_type: hybrid\n---\n") == "hybrid"
    assert _grading_type("---\nfoo: 1\n---\n") == "unknown"


def test_stage_all_small(repo_data_present, sample_task_ids, tmp_path):
    from benchmark.tools import stage as stage_mod
    task_ids = list(sample_task_ids)
    manifest = stage_mod.stage_all(task_ids, {"train": task_ids, "test": []}, tmp_path)
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "splits" / "train.json").exists()
    assert manifest["n_tasks"] >= 1
    # manifest.tasks 与磁盘目录一致
    for t in manifest["tasks"]:
        if t["status"] == "ok":
            assert (tmp_path / "tasks" / t["task_id"] / "gold_verifier" / "labels.json").exists()
