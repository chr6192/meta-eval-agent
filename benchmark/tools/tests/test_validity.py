from benchmark.tools import stage, validity


def test_validity_runs_and_reports(repo_data_present, sample_task_ids, tmp_path):
    ids = list(sample_task_ids)
    stage.stage_all(ids, {"train": ids, "test": []}, tmp_path)
    rep = validity.run(tmp_path)
    assert (tmp_path / "_stage" / "validity_report.md").exists()
    for k in ["v1_gold_consistency", "v2_discrimination", "v3_gt_sanity", "v4_reachable_weight"]:
        assert k in rep
    assert "grader_reads_gt_count" in rep["v3_gt_sanity"]
    assert "tasks_reading_gt" in rep["v3_gt_sanity"]


def test_v2_flags_degenerate(repo_data_present, sample_task_ids, tmp_path):
    ids = list(sample_task_ids)
    stage.stage_all(ids, {"train": ids, "test": []}, tmp_path)
    rep = validity.run(tmp_path)
    assert "per_task" in rep["v2_discrimination"]
    assert "low_discrimination" in rep["v2_discrimination"]
