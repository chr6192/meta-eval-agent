import json
from benchmark.tools import transcript_norm, paths


def test_normalize_real_transcript(repo_data_present, fixture_tasks, primary_candidate, tmp_path):
    cal = fixture_tasks["calendar"]
    base = paths.FRAMEWORK_BASES[primary_candidate]
    src = base / "transcripts" / f"{cal}.jsonl"
    if not src.exists():
        import pytest; pytest.skip("无此 transcript")
    out = tmp_path / "transcript.jsonl"
    n = transcript_norm.normalize_transcript(src, out)
    assert n > 0
    lines = out.read_text().strip().splitlines()
    assert len(lines) == n            # 不截断：行数 = 返回数
    for ln in lines:
        rec = json.loads(ln)
        assert "role" in rec
        assert rec["role"] in {"system", "user", "assistant", "tool"}


def test_normalize_synthetic_nested(tmp_path):
    src = tmp_path / "raw.jsonl"
    rows = [
        {"type": "message", "message": {"role": "system", "content": [{"type": "text", "text": "sys"}]}},
        {"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": "hi"}]}},
        {"type": "message", "timestamp": "T1", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "calling"},
            {"type": "toolCall", "name": "ls", "arguments": {"path": "/"}}]}},
        {"type": "message", "message": {"role": "toolResult", "content": [{"type": "toolResult", "output": "files"}]}},
        {"type": "message", "message": {"role": "weirdo", "content": [{"type": "text", "text": "x"}]}},
    ]
    src.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    out = tmp_path / "norm.jsonl"
    n = transcript_norm.normalize_transcript(src, out)
    recs = [json.loads(l) for l in out.read_text().strip().splitlines()]
    assert n == len(recs)
    assert [r["role"] for r in recs] == ["system", "user", "assistant", "tool"]  # weirdo (unknown role) dropped
    asst = recs[2]
    assert "calling" in asst["content"]      # text block preserved in content
    assert asst.get("tool_call")             # toolCall surfaced structurally
    assert asst.get("ts") == "T1"            # outer timestamp passthrough
