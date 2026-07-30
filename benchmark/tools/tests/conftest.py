import re

import pytest

from benchmark.tools import paths, lib, stage

# 新数据 (pawbench-v1.0) 代表性 task：task_id = frontmatter id:，与 results/workspaces 目录名一致
CALENDAR_TID = "01_Productivity_Flow_task_6_calendar_scheduling"  # hybrid + gt + oracle(optimality_ratio) + duration_respected
SAM3_TID = "02_Code_Intelligence_task_1_sam3_inference"            # hybrid + gt
PRIMARY_CANDIDATE = "qwenpaw__qwen3.6-plus"                         # 8 候选之一（calendar 在全部 8 个 model 都有 gt workspace）


def _find_automated_no_gt_task():
    """挑一个 grading_type=automated、官方 grader 不读 gt、且至少一个 candidate 跑过的真实 task id。"""
    for md in sorted(paths.TASKS_DIR.glob("*.md")):
        text = md.read_text(errors="ignore")
        if not re.search(r"^grading_type:\s*automated\s*$", text[:1500], re.M):
            continue
        tid_m = re.search(r"^id:\s*(\S+)", text[:600], re.M)
        if not tid_m:
            continue
        task_id = tid_m.group(1)
        if re.search(r"gt/|optimal_|ground[_.]?truth|reference_|expected_", text):
            continue   # 读 gt 的不算"无 gt"
        if any((base / "workspaces" / task_id).exists() for base in paths.FRAMEWORK_BASES.values()):
            return task_id
    return None


@pytest.fixture(scope="session")
def fixture_tasks():
    # 注：data 缺失时 "automated" 为 None；消费它的测试必须自行 guard（见各 test 的 skip）
    return {
        "calendar": CALENDAR_TID,   # hybrid + gt + oracle
        "sam3": SAM3_TID,           # gt
        "automated": _find_automated_no_gt_task(),
    }


@pytest.fixture(scope="session")
def primary_candidate():
    return PRIMARY_CANDIDATE


@pytest.fixture(scope="session")
def sample_task_ids():
    """少量可 stage 的真实 task id（替代旧的 SPLIT_DIR/train.json 视图读取）。"""
    return stage.discover_task_ids()[:3]


@pytest.fixture(scope="session")
def repo_data_present():
    """没有原始数据就跳过整套测试，而不是误报失败。"""
    if not paths.SRC_BENCH.exists():
        pytest.skip(f"原始数据缺失: {paths.SRC_BENCH}")
