"""唯一加载/运行 produced grader 的地方。健壮处理签名差异 + 异常 + 超时。"""
from __future__ import annotations
import importlib.util
import inspect
import multiprocessing
import os
import queue as queue_module
import sys
import traceback
import uuid
from pathlib import Path

# 与 judge_harness.py 的 VERIFIER_JUDGE_TIMEOUT_S 联动：agentic_judge 采样已改成并行
# （见 judge_harness.invoke_agentic_judge），单次 grade() 调用的墙钟时间上界约等于
# "judge 单样本 timeout_s + 少量并行/沙箱开销"，不再是 k 倍。这里默认用同一个环境变量
# 的值加 90s 余量（覆盖确定性层检查耗时 + 并行调度开销），两边任一时刻都可独立用各自
# 环境变量单独覆盖，但默认值保持数学上自洽（不会出现外层比内层还短的情况）。
DEFAULT_TIMEOUT_S = int(os.environ.get(
    "RUN_GRADER_TIMEOUT_S",
    str(int(os.environ.get("VERIFIER_JUDGE_TIMEOUT_S", "90")) + 90),
))


def _derive_passed(r: dict):
    if isinstance(r.get("outcome_passed"), bool):
        return r["outcome_passed"]
    if isinstance(r.get("passed"), bool):
        return r["passed"]
    for k in ("score", "overall_score", "total_score"):
        v = r.get(k)
        if isinstance(v, (int, float)):
            return float(v) >= 0.99
    return None


def _derive_score(r: dict):
    for k in ("score", "overall_score", "total_score"):
        v = r.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    bd = r.get("breakdown")
    if isinstance(bd, dict):
        vals = [v for v in bd.values() if isinstance(v, (int, float))]
        if vals:
            return sum(vals) / len(vals)
    return None


def _call(mod, transcript, workspace_path):
    ws = str(workspace_path)
    sig = inspect.signature(mod.grade)
    n_pos = sum(1 for p in sig.parameters.values()
                if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                              inspect.Parameter.POSITIONAL_ONLY))
    if n_pos >= 2:
        return mod.grade(transcript, ws)
    if n_pos == 1:
        return mod.grade(ws)
    return mod.grade(ws, None)


def _run_in_subprocess(grader_path: str, transcript: list, workspace_path: str, out_queue) -> None:
    """子进程体：import grader、跑 grade()、把结果序列化塞进 queue。"""
    name = f"produced_grader_{uuid.uuid4().hex}"
    try:
        gp = Path(grader_path)
        spec = importlib.util.spec_from_file_location(name, gp)
        mod = importlib.util.module_from_spec(spec)
        gp_dir = str(gp.parent)
        if gp_dir not in sys.path:
            sys.path.insert(0, gp_dir)
        spec.loader.exec_module(mod)
        r = _call(mod, transcript, workspace_path)
        if not isinstance(r, dict):
            out_queue.put({"outcome_passed": None, "score": None, "breakdown": {},
                           "criteria": [], "_error": f"non-dict {type(r).__name__}",
                           "judge_meta": None})
            return
        # judge_meta 是可选字段：verifier-author 生成的 grader.py 如果调用了
        # agentic_judge，约定把 invoke_agentic_judge() 的返回值原样放进这里
        # （{available, agreement, n_samples_ok, wall_time_s}），供评测侧记账
        # （Task D2）结构化读取，不必解析 notes 自由文本。没用到 agentic_judge
        # 的 grader 不需要写这个字段，get 到 None 即可。
        jm = r.get("judge_meta")
        out_queue.put({
            "outcome_passed": _derive_passed(r), "score": _derive_score(r),
            "breakdown": r.get("breakdown", {}) if isinstance(r.get("breakdown"), dict) else {},
            "criteria": r.get("criteria", []) if isinstance(r.get("criteria"), list) else [],
            "judge_meta": jm if isinstance(jm, dict) else None,
            "_error": None,
        })
    except Exception:
        out_queue.put({"outcome_passed": None, "score": None, "breakdown": {},
                       "criteria": [], "judge_meta": None,
                       "_error": traceback.format_exc(limit=4)})


def run(grader_path: Path, transcript: list, workspace_path: Path, timeout_s: int = DEFAULT_TIMEOUT_S) -> dict:
    """运行一个 produced grader，返回
    {outcome_passed, score, breakdown, criteria, judge_meta, _error}。

    在独立子进程里跑：agentic_judge 场景下 grade() 可能挂起在子进程调用上
    （如本地 agent CLI 卡死），必须能真正 kill 掉整个子进程树，同进程线程
    超时做不到这一点。
    """
    ctx = multiprocessing.get_context("spawn")
    result_queue: multiprocessing.Queue = ctx.Queue()
    proc = ctx.Process(
        target=_run_in_subprocess,
        args=(str(grader_path), transcript, str(workspace_path), result_queue),
    )
    proc.start()
    proc.join(timeout=timeout_s)
    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=5)
        if proc.is_alive():
            proc.kill()
            proc.join()
        return {"outcome_passed": None, "score": None, "breakdown": {}, "criteria": [],
                "judge_meta": None, "_error": f"timeout: grade() 未在 {timeout_s}s 内返回"}
    # proc.join() 返回只保证子进程已退出，不保证父进程侧的 Queue reader 线程
    # 已经把 pipe 里的数据搬进本地 deque（multiprocessing 已知陷阱）。用有限
    # 等待代替 get_nowait()，给 reader 线程一点缓冲时间，避免把"其实已经产出
    # 结果"的正常退出误判为"子进程异常退出"。
    try:
        return result_queue.get(timeout=5)
    except queue_module.Empty:
        return {"outcome_passed": None, "score": None, "breakdown": {}, "criteria": [],
                "judge_meta": None, "_error": f"子进程异常退出(exitcode={proc.exitcode})，未产出结果"}
