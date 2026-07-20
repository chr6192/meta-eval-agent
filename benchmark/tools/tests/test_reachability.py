from benchmark.tools import reachability, lib


def test_calendar_has_oracle_dim(repo_data_present, fixture_tasks):
    cal = fixture_tasks["calendar"]
    md = lib.resolve_task_md(cal)
    _, sections = lib.strip_task_md(md.read_text())
    grader_src = sections["automated_checks"]
    out = reachability.analyze(cal, grader_src, md.read_text())
    crits = {d["criterion"]: d for d in out["dimensions"]}
    # optimality_ratio 依赖 gt → oracle 不可达
    assert any(d["depends_on"] == "oracle" and not d["reachable"]
               for d in out["dimensions"]), "未识别出 oracle 维度"
    assert "optimality_ratio" in crits
    # optimality_ratio 仍是 oracle（读 gt）
    assert crits["optimality_ratio"]["depends_on"] == "oracle"
    # duration_respected 是纯 workspace 检查，不能被 "ratio" 子串误判成 oracle
    assert crits["duration_respected"]["depends_on"] == "workspace"
    assert crits["duration_respected"]["reachable"] is True
    assert 0.0 <= out["reachable_weight"] <= 1.0


def test_automated_task_mostly_reachable(repo_data_present, fixture_tasks):
    tid = fixture_tasks["automated"]
    if not tid:
        import pytest; pytest.skip("无 automated 无 gt 的样本")
    md = lib.resolve_task_md(tid)
    _, sections = lib.strip_task_md(md.read_text())
    out = reachability.analyze(tid, sections["automated_checks"] or "", md.read_text())
    # 纯 automated 无 gt：可达权重应较高
    assert out["reachable_weight"] >= 0.5


def test_classify_criterion_unit():
    from benchmark.tools.reachability import _classify_criterion
    assert _classify_criterion("optimality_ratio", True) == ("oracle", False)
    assert _classify_criterion("optimality_ratio", False) == ("workspace", True)   # 没读 gt 不算 oracle
    assert _classify_criterion("duration_respected", True) == ("workspace", True)
    assert _classify_criterion("multi_step_reasoning", True)[0] == "transcript"


def test_llm_judge_weight_unit():
    from benchmark.tools.reachability import _llm_judge_weight
    md = "---\ngrading_weights:\n  automated: 0.6\n  llm_judge: 0.4\ntimeout: 1\n---\n# x\n"
    assert abs(_llm_judge_weight(md) - 0.4) < 1e-9
    assert _llm_judge_weight("---\nfoo: 1\n---\n") == 0.0


def test_extraction_method_unit():
    from benchmark.tools.reachability import _extract_criteria
    src_all = "ALL_CRITERIA = ['a_b', 'c_d', 'overall_score']\ndef grade(t, w):\n    return {}\n"
    crits, method = _extract_criteria(src_all)
    assert method == "all_criteria"
    assert "overall_score" not in crits and "a_b" in crits
    empty, m2 = _extract_criteria("def grade(t, w):\n    return {}\n")
    assert m2 == "none" and empty == []


_FAKE_GRADER_SRC = (
    "ALL_CRITERIA = ['task_completed', 'optimal_route_used', 'overall_score']\n"
    "def grade(transcript, workspace):\n"
    "    return {}\n"
)

_FAKE_TASK_MD = (
    "---\n"
    "id: fake_task\n"
    "grading_type: hybrid\n"
    "grading_weights:\n"
    "  automated: 0.7\n"
    "  llm_judge: 0.3\n"
    "timeout: 60\n"
    "---\n"
    "# fake task\n"
)


def test_llm_judgment_unreachable_by_default():
    """默认不传 agentic_judge_capable：保持历史假设，llm-judgment 恒不可达。"""
    out = reachability.analyze("fake_task", _FAKE_GRADER_SRC, _FAKE_TASK_MD)
    dims = {d["criterion"]: d for d in out["dimensions"]}
    assert "__llm_judge_overall__" in dims
    assert dims["__llm_judge_overall__"]["depends_on"] == "llm-judgment"
    assert dims["__llm_judge_overall__"]["reachable"] is False
    # optimal_route_used 读 gt → oracle，仍不可达
    assert dims["optimal_route_used"]["depends_on"] == "oracle"
    assert dims["optimal_route_used"]["reachable"] is False
    # llm_w=0.3, oracle_frac=1/2=0.5 → (1-0.3)*(1-0.5) = 0.35
    assert abs(out["reachable_weight"] - 0.35) < 1e-9


def test_llm_judgment_reachable_when_agentic_judge_capable():
    """显式传 agentic_judge_capable=True：__llm_judge_overall__ 视为可达，权重不再被 llm_w 打折。"""
    out = reachability.analyze("fake_task", _FAKE_GRADER_SRC, _FAKE_TASK_MD,
                                agentic_judge_capable=True)
    dims = {d["criterion"]: d for d in out["dimensions"]}
    assert dims["__llm_judge_overall__"]["depends_on"] == "llm-judgment"
    assert dims["__llm_judge_overall__"]["reachable"] is True
    # oracle 维度不受 agentic_judge_capable 影响，仍不可达
    assert dims["optimal_route_used"]["depends_on"] == "oracle"
    assert dims["optimal_route_used"]["reachable"] is False
    # oracle_frac=0.5 → 1-0.5 = 0.5（不再乘 (1-llm_w)）
    assert abs(out["reachable_weight"] - 0.5) < 1e-9


def test_reachable_weight_formula_no_oracle_llm_w_examples():
    """llm_w=0.3、oracle_frac=0 时：默认应为 0.7，agentic_judge_capable=True 时应为 1.0。"""
    grader_src = "ALL_CRITERIA = ['task_completed', 'duration_respected']\ndef grade(t, w):\n    return {}\n"
    md = ("---\ngrading_weights:\n  automated: 0.7\n  llm_judge: 0.3\ntimeout: 1\n---\n# x\n")
    out_default = reachability.analyze("t2", grader_src, md)
    assert abs(out_default["reachable_weight"] - 0.7) < 1e-9
    out_agentic = reachability.analyze("t2", grader_src, md, agentic_judge_capable=True)
    assert abs(out_agentic["reachable_weight"] - 1.0) < 1e-9
