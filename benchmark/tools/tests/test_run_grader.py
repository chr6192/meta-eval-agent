from pathlib import Path
from benchmark.tools import run_grader


def _write(p: Path, src: str):
    p.write_text(src); return p


def test_run_normal_grader(tmp_path):
    g = _write(tmp_path / "grader.py",
               "def grade(transcript, workspace_path):\n"
               "    return {'outcome_passed': True, 'score': 0.8, 'breakdown': {'a': 1.0}}\n")
    r = run_grader.run(g, transcript=[], workspace_path=tmp_path)
    assert r["outcome_passed"] is True
    assert r["score"] == 0.8
    assert r["_error"] is None


def test_run_grader_score_only_derives_pass(tmp_path):
    g = _write(tmp_path / "grader.py",
               "def grade(transcript, workspace_path):\n"
               "    return {'overall_score': 1.0}\n")
    r = run_grader.run(g, transcript=[], workspace_path=tmp_path)
    assert r["score"] == 1.0
    assert r["outcome_passed"] is True


def test_run_grader_error_is_captured(tmp_path):
    g = _write(tmp_path / "grader.py",
               "def grade(transcript, workspace_path):\n"
               "    raise ValueError('boom')\n")
    r = run_grader.run(g, transcript=[], workspace_path=tmp_path)
    assert r["_error"] is not None
    assert r["outcome_passed"] is None
    assert r["score"] is None


def test_run_grader_legacy_signature(tmp_path):
    g = _write(tmp_path / "grader.py",
               "def grade(workspace_path):\n"
               "    return {'outcome_passed': False, 'score': 0.1}\n")
    r = run_grader.run(g, transcript=[], workspace_path=tmp_path)
    assert r["outcome_passed"] is False


def test_run_grader_breakdown_mean_score(tmp_path):
    g = _write(tmp_path / "grader.py",
               "def grade(transcript, workspace_path):\n"
               "    return {'breakdown': {'a': 0.8, 'b': 0.6}}\n")
    r = run_grader.run(g, transcript=[], workspace_path=tmp_path)
    assert abs(r["score"] - 0.7) < 1e-9   # 无显式 score → breakdown 均值
    assert r["_error"] is None


import time


def test_run_grader_times_out_on_hanging_grade(tmp_path):
    grader = tmp_path / "grader.py"
    grader.write_text(
        "import time\n"
        "def grade(transcript, workspace_path):\n"
        "    time.sleep(30)\n"
        "    return {'outcome_passed': True}\n"
    )
    t0 = time.time()
    result = run_grader.run(grader, [], str(tmp_path), timeout_s=2)
    elapsed = time.time() - t0
    assert elapsed < 10
    assert result["outcome_passed"] is None
    assert "timeout" in (result["_error"] or "").lower()


def test_run_grader_normal_case_still_works(tmp_path):
    grader = tmp_path / "grader.py"
    grader.write_text(
        "def grade(transcript, workspace_path):\n"
        "    return {'outcome_passed': True, 'score': 1.0}\n"
    )
    result = run_grader.run(grader, [], str(tmp_path), timeout_s=5)
    assert result["outcome_passed"] is True
    assert result["_error"] is None
    assert result["judge_meta"] is None  # 没用 agentic_judge 的 grader，此字段应为 None


def test_run_grader_passes_through_judge_meta(tmp_path):
    """grader.py 若在返回值里带 judge_meta（agentic_judge 的结构化元数据），
    run_grader.run 必须原样透传，供 Task D2 的账本读取，不需要解析 notes 文本。"""
    grader = tmp_path / "grader.py"
    grader.write_text(
        "def grade(transcript, workspace_path):\n"
        "    return {'outcome_passed': True, 'score': 0.8,\n"
        "            'judge_meta': {'available': True, 'agreement': 0.9,\n"
        "                           'n_samples_ok': 3, 'wall_time_s': 42.0}}\n"
    )
    result = run_grader.run(grader, [], str(tmp_path), timeout_s=5)
    assert result["judge_meta"] == {
        "available": True, "agreement": 0.9, "n_samples_ok": 3, "wall_time_s": 42.0,
    }
