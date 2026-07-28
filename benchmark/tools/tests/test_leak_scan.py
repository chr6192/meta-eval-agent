"""trajectory-based 反泄漏：只在 agent 实际工具调用触达 gold_verifier/ 时报泄漏。"""
import json
from benchmark.tools.leak_scan import scan_trajectory


def _tool_call(tool, args):
    return {"type": "tool_call", "tool_call": {tool: {"args": args}}}


def _user(text):
    return {"type": "user", "message": {"content": text}}


def test_clean_when_only_reads_inputs():
    traj = [
        _user("禁止打开 .../gold_verifier/ （prompt 里提到也不算泄漏）"),
        _tool_call("readToolCall", {"path": "/repo/tasks/T1/verifier_author_inputs/task_md.md"}),
    ]
    assert scan_trajectory(traj) == []


def test_flags_gold_read():
    traj = [
        _tool_call("readToolCall", {"path": "/repo/tasks/T1/gold_verifier/labels.json"}),
    ]
    v = scan_trajectory(traj)
    assert len(v) == 1 and v[0]["tool"] == "readToolCall" and "gold_verifier/" in v[0]["path"]


def test_flags_shell_touching_gold():
    traj = [_tool_call("shellToolCall", {"command": "cat tasks/T1/gold_verifier/official_grader.py"})]
    assert len(scan_trajectory(traj)) == 1


def test_prompt_mention_not_flagged():
    # 仅 user/assistant 文本提到 gold 路径，无工具调用 → 干净
    traj = [_user("绝不读取 tasks/T1/gold_verifier/official_rubric.md")]
    assert scan_trajectory(traj) == []


def test_accepts_jsonl_string():
    lines = "\n".join(json.dumps(e) for e in [
        _tool_call("readToolCall", {"path": "/x/gold_verifier/reachability.json"})])
    assert len(scan_trajectory(lines)) == 1


# --- 兜底：历史/同轮其它 task 的 produced verifier（runs/<label>/produced/）---

def test_flags_produced_read_relative():
    traj = [_tool_call("readToolCall", {"path": "runs/iter_0/produced/T1/grader.py"})]
    v = scan_trajectory(traj)
    assert len(v) == 1 and v[0]["kind"] == "produced"


def test_flags_produced_read_absolute():
    traj = [_tool_call("shellToolCall",
                       {"command": "cat /Users/x/exp/260622/runs/iter_2/produced/T1/grader.py"})]
    v = scan_trajectory(traj)
    assert len(v) == 1 and v[0]["kind"] == "produced"


def test_sandbox_own_produced_not_flagged():
    # 沙箱自身的 ./produced/ 写出不是泄漏：路径不含 runs/<label>/produced/
    traj = [
        _tool_call("writeToolCall", {"path": "produced/grader.py"}),
        _tool_call("writeToolCall", {"path": "/tmp/vauthor.T1.iter_0.abc/produced/rubric.md"}),
    ]
    assert scan_trajectory(traj) == []


def test_gold_hit_tagged_kind():
    traj = [_tool_call("readToolCall", {"path": "/repo/tasks/T1/gold_verifier/labels.json"})]
    assert scan_trajectory(traj)[0]["kind"] == "gold"
