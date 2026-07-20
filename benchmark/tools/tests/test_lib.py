from benchmark.tools import paths
from benchmark.tools import lib


def test_paths_resolve(repo_data_present):
    assert paths.TASKS_DIR.exists()
    assert paths.ASSETS_DIR.exists()
    assert isinstance(paths.CANDIDATE_SPECS, list)
    assert len(paths.CANDIDATE_SPECS) == len(paths.MODELS)
    assert {s["key"] for s in paths.CANDIDATE_SPECS} == set(paths.FRAMEWORK_BASES)
    for spec in paths.FRAMEWORK_BASES.values():
        assert spec.exists(), f"framework base 缺失: {spec}"


def test_strip_scoring_sections(repo_data_present, fixture_tasks):
    md = lib.resolve_task_md(fixture_tasks["calendar"])
    assert md is not None
    text = md.read_text()
    stripped, sections = lib.strip_task_md(text)
    # 评分侧段全部被剥离
    for header in ["## Automated Checks", "## Grading Criteria",
                   "## LLM Judge Rubric", "## Expected Behavior"]:
        assert header not in stripped, f"{header} 未被剥离"
    # Prompt 段保留
    assert "## Prompt" in stripped
    # 剥下来的段被收集
    assert sections["automated_checks"] is not None
    assert "def grade" in sections["automated_checks"]


def test_strip_removes_scoring_frontmatter(repo_data_present, fixture_tasks):
    md = lib.resolve_task_md(fixture_tasks["calendar"])
    stripped, _ = lib.strip_task_md(md.read_text())
    assert "grading_weights:" not in stripped
    assert "grading_type:" not in stripped
    # 环境字段保留
    assert "workspace_files:" in stripped


def test_strip_task_md_unit():
    sample = (
        "---\n"
        "id: demo\n"
        "grading_type: hybrid\n"
        "grading_weights:\n"
        "  automated: 0.6\n"
        "  llm_judge: 0.4\n"
        "workspace_files:\n"
        "  - source: a.txt\n"
        "timeout_seconds: 120\n"
        "---\n"
        "\n## Prompt\ndo the thing\n"
        "\n## Expected Behavior\nit works\n"
        "\n## Grading Criteria\ncrit\n"
        "\n## Automated Checks\n```python\ndef grade(transcript, workspace_path):\n    return {}\n```\n"
        "\n## LLM Judge Rubric\njudge it\n"
    )
    stripped, sections = lib.strip_task_md(sample)
    for h in ["## Automated Checks", "## Grading Criteria", "## LLM Judge Rubric", "## Expected Behavior"]:
        assert h not in stripped
    assert "## Prompt" in stripped
    assert "workspace_files:" in stripped
    assert "timeout_seconds: 120" in stripped
    assert "grading_type:" not in stripped
    assert "grading_weights:" not in stripped
    assert "automated: 0.6" not in stripped
    assert "def grade" in sections["automated_checks"]
    assert "```" not in sections["automated_checks"]   # 围栏已剥离
    import ast as _ast
    _ast.parse(sections["automated_checks"])           # 是合法 Python
    assert sections["grading_criteria"] is not None
    assert sections["llm_judge_rubric"] is not None
    assert sections["expected_behavior"] is not None


def test_load_framework_results(repo_data_present, fixture_tasks):
    res = lib.load_framework_results()
    assert set(res.keys()) == set(paths.FRAMEWORK_BASES.keys())
    cal = fixture_tasks["calendar"]
    # calendar 至少在一个 candidate 有跑分
    assert any(cal in res[k] for k in res)


def test_build_workspace_isolated_removes_gt(repo_data_present, fixture_tasks, primary_candidate, tmp_path):
    cal = fixture_tasks["calendar"]
    dst = tmp_path / "ws"
    ok = lib.build_one_workspace(cal, primary_candidate, dst, keep_gt=False)
    if not ok:
        import pytest; pytest.skip("该 candidate 无此 task 的 workspace")
    # 隔离版：不得有 gt 目录或 optimal_* 文件
    assert not any(p.name == "gt" for p in dst.rglob("*"))
    assert not any("optimal_" in p.name for p in dst.rglob("*"))
    bad_prefixes = ("optimal_", "expected_", "reference_", "solution_", "answer_", "golden_", "ground_truth")
    assert not any(p.is_file() and p.name.startswith(bad_prefixes) for p in dst.rglob("*"))
    # runtime noise 已过滤
    assert not (dst / "AGENTS.md").exists()


def test_build_workspace_keepgt_has_gt(repo_data_present, fixture_tasks, primary_candidate, tmp_path):
    cal = fixture_tasks["calendar"]
    dst = tmp_path / "ws_gt"
    ok = lib.build_one_workspace(cal, primary_candidate, dst, keep_gt=True)
    if not ok:
        import pytest; pytest.skip("该 candidate 无此 task 的 workspace")
    assert (dst / "gt" / "optimal_unscheduled.json").exists()


def test_automated_checks_is_valid_python(repo_data_present, fixture_tasks):
    import ast
    md = lib.resolve_task_md(fixture_tasks["calendar"])
    _, sections = lib.strip_task_md(md.read_text())
    src = sections["automated_checks"]
    assert "```" not in src        # 围栏已剥离
    ast.parse(src)                 # 合法 Python，不抛 SyntaxError
    assert "def grade" in src


def test_strip_filters_gt_from_workspace_files():
    sample = (
        "---\n"
        "id: demo\n"
        "workspace_files:\n"
        "  - source: demo/gt/optimal_x.json\n"
        "    dest: gt/optimal_x.json\n"
        "  - source: calendar.ics\n"
        "    dest: calendar.ics\n"
        "timeout_seconds: 60\n"
        "---\n"
        "\n## Prompt\ndo it\n"
    )
    stripped, _ = lib.strip_task_md(sample)
    # GT 条目被删，普通条目保留
    assert "gt/optimal_x.json" not in stripped
    assert "optimal_x" not in stripped
    assert "calendar.ics" in stripped
    assert "timeout_seconds: 60" in stripped
    # 重新解析 workspace_files：不得有 GT 条目
    from pathlib import Path as _P
    for item in lib.parse_workspace_files(stripped):
        for v in (item.get("source", ""), item.get("dest", "")):
            assert not (v and lib.is_gt_path(_P(v))), f"残留 GT 条目 {v}"
