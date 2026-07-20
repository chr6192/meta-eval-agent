#!/usr/bin/env python3
"""重新生成 examples/quickstart/bench/ 里的 10 个 demo task。

前提：本机 origin_data/ 下已有完整 pawbench-v1.0 原始数据（本仓库不分发这份数据，
见根目录 README「数据与许可」一节）。没有原始数据就不需要跑这个脚本——
examples/quickstart/bench/ 已经是跑好的产物，直接用即可。

用法（在仓库根目录执行）：
    python examples/quickstart/scripts/stage_demo.py
"""
from __future__ import annotations
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from benchmark.tools import stage  # noqa: E402

# 6 个 open-ended（无单一标准答案，需要主观归纳评分维度）task，均来自上游
# pinchbench 子来源（同一命名风格：task_<slug>，见 origin_data/SOURCES.md），
# 且是 260701_agenticjudge 实验里 verifier-author 表现较好、较稳定的一批：
# 写作（task_blog）、法律分析（task_contract_analysis）、会议纪要提取 x2
# （task_meeting_advisory_attendees / task_meeting_gov_data_sources）、
# 视频转写摘要（task_video_transcript_extraction）、issue 分诊排序
# （task_gh_issue_triage）。选取标准：同命名家族、grading 依赖主观判断、
# 物化后单 task 体积可接受（<10MB），便于直接随代码仓库分发。
DEMO_TASK_IDS = [
    "task_blog",
    "task_contract_analysis",
    "task_meeting_advisory_attendees",
    "task_video_transcript_extraction",
    "task_meeting_gov_data_sources",
    "task_gh_issue_triage",
]


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "bench"
    manifest = stage.stage_all(DEMO_TASK_IDS, {"demo": DEMO_TASK_IDS}, out)
    print(f"[stage_demo] {manifest['n_tasks']}/{len(DEMO_TASK_IDS)} 个 task -> {out}")
    for entry in manifest["tasks"]:
        print(f"  - {entry['task_id']}: {entry['status']} "
              f"({len(entry.get('candidates', []))} candidates)")


if __name__ == "__main__":
    main()
