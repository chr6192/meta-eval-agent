from benchmark.tools import stage, self_test


def test_self_test_passes_on_clean_stage(repo_data_present, sample_task_ids, tmp_path):
    ids = list(sample_task_ids)
    stage.stage_all(ids, {"train": ids, "test": []}, tmp_path)
    report = self_test.run(tmp_path)
    assert report["passed"], report["failures"]
    assert (tmp_path / "_stage" / "self_test_report.md").exists()


def test_self_test_catches_gt_leak(repo_data_present, sample_task_ids, tmp_path):
    ids = list(sample_task_ids[:1])
    stage.stage_all(ids, {"train": ids, "test": []}, tmp_path)
    # 人为往 author 输入层塞一个 GT 文件
    bad = tmp_path / "tasks" / ids[0] / "verifier_author_inputs" / "gt"
    bad.mkdir(parents=True, exist_ok=True)
    (bad / "optimal_x.json").write_text("{}")
    report = self_test.run(tmp_path)
    assert not report["passed"]
    assert any("gt/" in f for f in report["failures"])


def test_self_test_catches_missing_gold_file(repo_data_present, sample_task_ids, tmp_path):
    ids = list(sample_task_ids[:1])
    stage.stage_all(ids, {"train": ids, "test": []}, tmp_path)
    (tmp_path / "tasks" / ids[0] / "gold_verifier" / "reachability.json").unlink()
    report = self_test.run(tmp_path)
    assert not report["passed"]
    assert any("reachability.json" in f for f in report["failures"])


def test_self_test_catches_workspace_files_gt_leak(repo_data_present, sample_task_ids, tmp_path):
    ids = list(sample_task_ids[:1])
    stage.stage_all(ids, {"train": ids, "test": []}, tmp_path)
    md = tmp_path / "tasks" / ids[0] / "verifier_author_inputs" / "task_md.md"
    # 人为往 task_md 注入一个 GT workspace_files 条目
    txt = md.read_text()
    inject = "\nworkspace_files:\n  - source: x/gt/optimal_y.json\n    dest: gt/optimal_y.json\n"
    # 注入到 frontmatter 内（在第一个 --- 之后）
    parts = txt.split("---", 2)
    if len(parts) >= 3:
        md.write_text(parts[0] + "---" + parts[1] + inject + "---" + parts[2])
    else:
        md.write_text(txt + inject)
    report = self_test.run(tmp_path)
    assert not report["passed"]
    assert any("workspace_files" in f and "GT" in f for f in report["failures"])
