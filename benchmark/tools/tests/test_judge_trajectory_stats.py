# benchmark/tools/tests/test_judge_trajectory_stats.py
import json
from benchmark.tools import judge_trajectory_stats as jts


def test_scan_counts_files_and_observation_dirs(tmp_path):
    (tmp_path / "T001" / "c1").mkdir(parents=True)
    (tmp_path / "T001" / "c1" / "a.jsonl").write_text('{"type":"result"}\n')
    (tmp_path / "T001" / "c1" / "b.jsonl").write_text('{"type":"result"}\n')
    (tmp_path / "T002" / "c1").mkdir(parents=True)
    (tmp_path / "T002" / "c1" / "a.jsonl").write_text('{"type":"result"}\n')

    stats = jts.scan(tmp_path)
    assert stats["total_files"] == 3
    assert stats["total_observations_with_judge"] == 2  # 两个 (task,candidate) 目录


def test_scan_handles_empty_or_missing_root(tmp_path):
    missing = tmp_path / "does_not_exist"
    stats = jts.scan(missing)
    assert stats["total_files"] == 0
    assert stats["total_observations_with_judge"] == 0


def test_scan_flags_leak_hits_via_leak_scan(tmp_path):
    """轨迹里若出现触达禁区路径的工具调用（复用 leak_scan.scan_trajectory 的判定
    口径），必须在统计里体现出来，供人工复核——这是复用既有反泄漏机制的
    defense-in-depth，之前 agentic_judge 子进程完全没有这层复核。"""
    d = tmp_path / "T001" / "c1"
    d.mkdir(parents=True)
    leaking = json.dumps({
        "type": "tool_call",
        "tool_call": {"read_file": {"args": {"path": "gold_verifier/labels.json"}}},
    })
    (d / "a.jsonl").write_text(leaking + "\n")

    stats = jts.scan(tmp_path)
    assert stats["leak_hits"] == 1


def test_render_produces_readable_report(tmp_path):
    (tmp_path / "T001" / "c1").mkdir(parents=True)
    (tmp_path / "T001" / "c1" / "a.jsonl").write_text('{"type":"result"}\n')
    stats = jts.scan(tmp_path)
    report = jts.render(stats)
    assert "触发过 agentic_judge 的观测数" in report
    assert "1" in report
