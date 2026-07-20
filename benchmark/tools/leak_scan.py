"""反信息泄漏：扫 verifier-author agent 的轨迹，判断它是否触达禁区路径。

两类禁区（口径一致：只看 agent **实际发起的工具调用 args**，不看 prompt 文本，
故零启发式、零误报——「读了就是读了，没读就是没读」）：
- gold：答案唯一真相目录 `gold_verifier/`。author 写 grader 期间触达即泄漏。
- produced：历史/同轮其它 task 的已生成 verifier，落在实验 runs 树下的
  `runs/<label>/produced/`。轻量沙箱方案下 author cwd=沙箱、产物写沙箱内 `./produced/`，
  故任何命中 `runs/<label>/produced/` 的访问都是越界偷读历史 verifier（数据泄漏）。
  用正则限定 `runs/<label>/produced/`，不误伤沙箱自身的 `./produced/` 写出。

输入：cursor-agent `--output-format stream-json` 的事件流（JSONL 文本，或已解析的事件列表）。
"""
from __future__ import annotations
import json
import re
from pathlib import Path

GOLD_MARKER = "gold_verifier/"
# 历史 produced verifier：runs/<迭代标签>/produced/ 。限定 runs/.../produced 段，
# 避免命中沙箱本地的 ./produced/（无 runs/<label>/ 前缀）。
PRODUCED_RE = re.compile(r"runs/[^/\s\"']+/produced/")


def _classify(s: str):
    """返回字符串命中的泄漏类型（gold 优先）；都不命中返回 None。"""
    if GOLD_MARKER in s:
        return "gold"
    if PRODUCED_RE.search(s):
        return "produced"
    return None


def _iter_events(trajectory) -> list[dict]:
    if isinstance(trajectory, list):
        return [e for e in trajectory if isinstance(e, dict)]
    events = []
    for line in str(trajectory).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _strings(node):
    """递归取出结构里的所有字符串值。"""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _strings(v)


def scan_trajectory(trajectory) -> list[dict]:
    """返回泄漏命中列表 [{"tool","path","kind"}]；空 = 干净。kind ∈ {gold, produced}。

    只检查 `tool_call` 事件里 agent 选择的工具入参（args），命中禁区路径即记一条。
    """
    violations = []
    for ev in _iter_events(trajectory):
        if ev.get("type") != "tool_call":
            continue
        tc = ev.get("tool_call", {})
        if not isinstance(tc, dict):
            continue
        for tool_name, body in tc.items():
            args = body.get("args") if isinstance(body, dict) else None
            if args is None:
                continue
            for s in _strings(args):
                kind = _classify(s)
                if kind:
                    violations.append({"tool": tool_name, "path": s, "kind": kind})
                    break
    return violations


def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="扫 author 轨迹是否触达 gold_verifier/ 或 runs/<label>/produced/ 历史 verifier"
                    "（退出码 0=干净, 11=泄漏, 2=输入错误）")
    ap.add_argument("trajectory", nargs="+", help="cursor-agent stream-json 轨迹文件（可多个）")
    a = ap.parse_args()
    total = 0
    for p in a.trajectory:
        path = Path(p)
        if not path.exists():
            print(f"[err] 轨迹不存在: {p}"); return 2
        vs = scan_trajectory(path.read_text(errors="ignore"))
        if vs:
            total += len(vs)
            print(f"[LEAK] {p}: {len(vs)} 处触达禁区")
            for v in vs:
                print(f"  - [{v['kind']}] {v['tool']}: {v['path']}")
        else:
            print(f"[ok] {p}: clean")
    return 11 if total else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
