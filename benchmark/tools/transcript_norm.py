"""三 harness 原始轨迹 → 统一 unified-message jsonl。不截断、不摘要。

注：content 是所有 block 的无损完整序列化（grader 当 freeform 文本读时能看到全部）；tool_call / tool_result 是结构化便利提取。toolCall block 会同时出现在 content 和 tool_call 中——这是有意的无损双视图，不是 bug。"""
from __future__ import annotations
import json
from pathlib import Path


def _extract_content_text(content) -> str:
    """从 content 字段提取文本字符串。
    兼容：str / list[{type, text/toolCall/...}] / dict / 其它。
    列表模式下把多个 block 合并：text block → 原文；toolCall block → json 序列化。
    """
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                parts.append(str(block))
                continue
            btype = block.get("type", "")
            if btype == "text":
                parts.append(block.get("text", ""))
            elif btype == "toolCall":
                parts.append(json.dumps(block, ensure_ascii=False))
            elif btype == "toolResult":
                parts.append(json.dumps(block, ensure_ascii=False))
            else:
                # unknown block type — serialize whole block
                parts.append(json.dumps(block, ensure_ascii=False))
        return "\n".join(p for p in parts if p)
    return ""


def _extract_tool_calls(content) -> list | None:
    """从 content list 中提取所有 toolCall block，返回 list 或 None。"""
    if not isinstance(content, list):
        return None
    calls = [b for b in content if isinstance(b, dict) and b.get("type") == "toolCall"]
    return calls if calls else None


def _norm_one(raw: dict) -> dict | None:
    """把一条原始 message 归一化。无法识别 role 的丢弃（返回 None）。

    支持两种封装格式：
    1. 扁平格式（role 在顶层）：{"role": "...", "content": ...}
    2. 嵌套格式（openclaw/copaw/hermes 实际格式）：
       {"type": "message", "message": {"role": "...", "content": [...]}}
    """
    # ---- 解包嵌套格式 ----
    if raw.get("type") == "message" and "message" in raw:
        inner = raw["message"]
        # 把 hermes 顶层 timestamp 透传给 inner（如果 inner 里没有）
        if "timestamp" in raw and "timestamp" not in inner:
            inner = dict(inner, timestamp=raw["timestamp"])
        return _norm_one(inner)

    # ---- 扁平格式处理 ----
    role = raw.get("role") or raw.get("type")
    if role == "human":
        role = "user"
    if role in ("ai", "model"):
        role = "assistant"
    # toolResult 是 openclaw/copaw/hermes 使用的 role 名 → 归一化为 "tool"
    if role == "toolResult" or raw.get("toolResult") is not None:
        role = "tool"
    if role not in {"system", "user", "assistant", "tool"}:
        return None

    rec: dict = {"role": role}

    # content：兼容 str / list / {text}
    content = raw.get("content", raw.get("text", ""))
    rec["content"] = _extract_content_text(content)

    if raw.get("thinking"):
        rec["thinking"] = raw["thinking"]

    # tool_call：从 content list 中提取 toolCall blocks，或从顶层字段
    # 结构化便利提取；同样的 block 也无损保留在 content 里（见模块 docstring）
    tool_calls = _extract_tool_calls(content) if isinstance(content, list) else None
    if tool_calls:
        rec["tool_call"] = tool_calls
    elif raw.get("toolCall") or raw.get("tool_call"):
        rec["tool_call"] = raw.get("toolCall") or raw.get("tool_call")

    if raw.get("toolResult") or raw.get("tool_result"):
        rec["tool_result"] = raw.get("toolResult") or raw.get("tool_result")

    ts = raw.get("timestamp") or raw.get("ts")
    if ts:
        rec["ts"] = ts

    return rec


def normalize_transcript(src_jsonl: Path, dst_jsonl: Path) -> int:
    """读原始 jsonl，逐行归一化写出。返回写出的行数。不删减内容。"""
    dst_jsonl.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(src_jsonl, errors="ignore") as fin, open(dst_jsonl, "w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            rec = _norm_one(raw)
            if rec is None:
                continue
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n
