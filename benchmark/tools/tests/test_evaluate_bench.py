import shutil
import pytest
from benchmark.tools import evaluate_bench, stage, paths


@pytest.fixture(scope="module")
def staged_with_produced(tmp_path_factory):
    if not paths.SRC_BENCH.exists():
        pytest.skip("原始数据缺失")
    out = tmp_path_factory.mktemp("bench")
    ids = stage.discover_task_ids()[:3]
    stage.stage_all(ids, {"train": ids, "test": []}, out)
    produced = tmp_path_factory.mktemp("produced")
    for tid in ids:
        og = out / "tasks" / tid / "gold_verifier" / "official_grader.py"
        if og.exists():
            (produced / tid).mkdir(parents=True)
            shutil.copy(og, produced / tid / "grader.py")
    return out, produced, ids


def test_evaluate_end_to_end(staged_with_produced):
    out, produced, ids = staged_with_produced
    # 注：官方 grader 跑在 GT 隔离 workspace 上多数返回不可 derive 的结果（derived=None）。
    # 本测试只验证"真实 grader 不崩 + 报告结构完整"；指标计算的真正覆盖见 test_evaluate_synthetic_computes_metrics。
    rep = evaluate_bench.evaluate(out, produced, "train")
    for k in ["d1", "d1_prime", "d2", "d3", "reachability", "n_obs",
              "coverage", "d1_score_threshold", "n_tasks"]:
        assert k in rep
    assert rep["n_obs"] > 0
    assert rep["d1"]["micro"] is None or 0.0 <= rep["d1"]["micro"] <= 1.0


def test_evaluate_writes_report(staged_with_produced, tmp_path):
    out, produced, ids = staged_with_produced
    rep = evaluate_bench.evaluate(out, produced, "train", report_dir=tmp_path)
    assert (tmp_path / "eval_report.md").exists()
    assert (tmp_path / "eval_per_obs.jsonl").exists()


def test_evaluate_missing_produced_grader_is_skipped(staged_with_produced, tmp_path):
    out, _produced, ids = staged_with_produced
    empty = tmp_path / "empty_produced"
    empty.mkdir()
    rep = evaluate_bench.evaluate(out, empty, "train")
    assert rep["d1"]["n"] == 0


def test_evaluate_synthetic_computes_metrics(staged_with_produced, tmp_path):
    """用确定性合成 grader，证明 evaluator 真的把 D1/D2/D3 算出来（非 None）。"""
    out, _official, ids = staged_with_produced
    synth = tmp_path / "synth_produced"
    for tid in ids:
        (synth / tid).mkdir(parents=True)
        # 按 candidate workspace 是否存在某文件给不同分，制造 candidate 间差异（让 D3 有对可比）
        (synth / tid / "grader.py").write_text(
            "import os\n"
            "def grade(transcript, workspace_path):\n"
            "    n = sum(1 for _ in os.scandir(workspace_path)) if os.path.isdir(workspace_path) else 0\n"
            "    score = min(1.0, n / 10.0)\n"
            "    return {'outcome_passed': score >= 0.3, 'score': score, 'breakdown': {'file_count': score}}\n")
    rep = evaluate_bench.evaluate(out, synth, "train")
    assert rep["n_obs"] > 0
    assert rep["d1"]["n"] == rep["n_obs"]                 # 所有 obs 可比（synth 不会 None）
    assert rep["d1"]["micro"] is not None and 0.0 <= rep["d1"]["micro"] <= 1.0
    assert rep["d2"]["mae"] is not None                   # score 对齐算出来了
    assert rep["d3"]["n_pairs"] >= 0                      # 排序维度跑通
    assert rep["reachability"]["raw_macro"] is not None
    assert rep["coverage"]["comparable_rate"] is not None
    assert rep["d1_score_threshold"]["micro"] is not None
