# verifier-author skill runtime: judge_harness.py
"""agentic_judge 运行时库。

由 skill 一次性提供，逐字节拷贝进产物目录使用——不由 verifier-author 现写。
grader.py 只 import 本文件、传参数，不重新实现沙箱/子进程/投票逻辑。

设计约束：
- stdlib only（不引入任何第三方依赖）
- 不出现任何 bench 专属路径名
- 沙箱隔离靠物理拷贝，不靠路径黑名单
- 支持两种证据来源：workspace_path（候选产物）与 transcript（候选执行轨迹），
  可以只给一个，也可以两个都给
- 任何失败都归一化为 available=False，永不抛异常给调用方
- 若 VERIFIER_JUDGE_LOG_DIR 环境变量给定，每次调用的完整轨迹会落盘到该目录——
  这是"调用发生过"唯一的事实凭据，不依赖调用方（grader.py）自己上报统计数字；
  不给这个环境变量时完全不落盘，零额外开销（生产环境默认不开）
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

DEFAULT_AGENT_CMD = os.environ.get("VERIFIER_JUDGE_CMD", "cursor-agent")
DEFAULT_MODEL = os.environ.get("VERIFIER_JUDGE_MODEL", "composer-2.5")
DEFAULT_TIMEOUT_S = int(os.environ.get("VERIFIER_JUDGE_TIMEOUT_S", "90"))
DEFAULT_K = int(os.environ.get("VERIFIER_JUDGE_K", "3"))
DEFAULT_MIN_AGREEMENT = float(os.environ.get("VERIFIER_JUDGE_MIN_AGREEMENT", "0.6"))


def _materialize_transcript(dest_path: Path, transcript: Any) -> None:
    """把 transcript 落盘成 sandbox 里的 transcript.jsonl。

    transcript 可以是：磁盘上已有 jsonl 文件的路径字符串，或已解析的 message dict 列表。
    """
    if isinstance(transcript, (str, os.PathLike)):
        src = Path(transcript)
        if src.exists():
            shutil.copy(str(src), dest_path)
        return
    if isinstance(transcript, list):
        with open(dest_path, "w", encoding="utf-8") as f:
            for msg in transcript:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        return
    raise TypeError("transcript 必须是文件路径字符串或 dict 列表")


def _copytree_no_symlinks(src: Path, dest: Path) -> int:
    """递归拷贝目录树，遇到符号链接直接跳过；返回跳过的链接数。

    两种"默认"行为都不够安全：shutil.copytree 默认 symlinks=False 会解引用并把
    链接目标的真实内容拷进沙箱——如果目标在沙箱树之外，等于把外部内容偷偷拉了进来；
    symlinks=True 会原样保留链接——沙箱里跑的裁判子进程如果真的去读这个链接，
    操作系统会照常追踪到外部，等于留了一条越界通道。两者都不做：遇到符号链接就跳过
    并计数，调用方可据此记录警告，但不阻断整体拷贝。
    """
    dest.mkdir(parents=True, exist_ok=True)
    skipped = 0
    for entry in src.iterdir():
        target = dest / entry.name
        if entry.is_symlink():
            skipped += 1
            continue
        if entry.is_dir():
            skipped += _copytree_no_symlinks(entry, target)
        elif entry.is_file():
            shutil.copy2(entry, target)
    return skipped


def _build_sandbox(workspace_path: str | None = None, transcript: Any = None) -> Path:
    """把候选证据物理拷贝进独立临时目录；子进程只能看到这个拷贝。

    workspace_path（若给）拷进 sandbox/workspace/；transcript（若给）落盘成
    sandbox/transcript.jsonl。子进程 cwd 会设为这个临时目录，其父目录之外的
    任何路径对子进程物理不存在（因为这是全新 tempdir，不是原目录树的子目录）。
    拷贝时跳过所有符号链接（见 `_copytree_no_symlinks`），防止候选 workspace 里
    偶然/恶意的链接把沙箱外内容拉进来或留下可追踪的越界通道。
    """
    sandbox = Path(tempfile.mkdtemp(prefix="judge_sandbox_"))
    if workspace_path is not None:
        dest = sandbox / "workspace"
        src = Path(workspace_path)
        if src.is_dir():
            _copytree_no_symlinks(src, dest)
        else:
            dest.mkdir(parents=True, exist_ok=True)
    if transcript is not None:
        _materialize_transcript(sandbox / "transcript.jsonl", transcript)
    return sandbox


def _write_spec_file(sandbox: Path, judge_prompt: str, schema: dict) -> Path:
    spec = {"instructions": judge_prompt, "output_schema": schema}
    path = sandbox / "_judge_spec.json"
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _describe_available_evidence(sandbox: Path) -> str:
    parts = []
    if (sandbox / "workspace").is_dir():
        parts.append("./workspace/ 下是候选产物（workspace 最终状态）")
    if (sandbox / "transcript.jsonl").exists():
        parts.append("./transcript.jsonl 是候选的执行轨迹（每行一条 JSON 消息，按时间顺序）")
    return "；".join(parts) if parts else "（无证据文件，仅凭 instructions 判断）"


def _persist_trajectory(log_dir: str, proc: Any) -> None:
    """把子进程的 stdout（stream-json 轨迹）落盘，供实验后统计与反泄漏复核用。

    这是唯一"agentic_judge 调用真的发生过"的事实凭据——不依赖 grader.py 自己
    上报统计数字（那样容易漏记，也不符合"基于事实行为而非自我上报"的原则）。
    任何落盘失败（目录不可写等）都静默忽略：这只是可选的审计副产物，绝不能因为
    落盘失败反过来影响裁判本身的可用性。
    """
    try:
        d = Path(log_dir)
        d.mkdir(parents=True, exist_ok=True)
        name = f"{time.time():.6f}_{uuid.uuid4().hex[:8]}.jsonl"
        text = getattr(proc, "stdout", None) or ""
        (d / name).write_text(text, encoding="utf-8", errors="replace")
    except OSError:
        pass


def _looks_like_score_object(value: Any) -> bool:
    """判断一个值本身是不是"单个维度的分数对象"（含 score 字段）。"""
    return isinstance(value, dict) and "score" in value


def _looks_like_dimension_collection(nested: dict, dims: list[str]) -> bool:
    """判断 parsed["dimensions"] 这个嵌套 dict 是不是"一堆维度的集合"（外壳包裹），
    而不是恰好某个维度真的叫 "dimensions" 且其值就是一个单独的分数对象。

    优先排除：nested 自身就长得像分数对象（直接含 "score" key）时，一律不当作外壳——
    这种情况下 "dimensions" 应该被当成普通维度名，值就是它自己的分数对象。
    再判定：nested 的 key 与 schema 里的维度名有重叠，或 nested 里有值长得像分数对象，
    才认为这是外壳包裹，需要展开。
    """
    if _looks_like_score_object(nested):
        return False
    if any(dim in nested for dim in dims):
        return True
    return any(_looks_like_score_object(v) for v in nested.values())


def _normalize_parsed_result(parsed: Any, schema: dict) -> dict[str, Any] | None:
    """把模型输出规整成 {dim: {"score": float, "evidence": str}}。

    兼容几种真实观测到的形状：
    - {"dimensions": {...}}（按 schema 外包一层）
    - {"dim_a": 1, "evidence": "..."}（维度值给成标量分数）
    - 标准形状 {"dim_a": {"score": 1, "evidence": "..."}}
    """
    if not isinstance(parsed, dict):
        return None

    dims = list(schema.get("dimensions", {}).keys())
    candidate: Any = parsed
    nested = parsed.get("dimensions")
    if isinstance(nested, dict) and _looks_like_dimension_collection(nested, dims):
        candidate = nested
    if not isinstance(candidate, dict):
        return None

    if not dims:
        return candidate

    fallback_evidence = ""
    for ev_src in (candidate.get("evidence"), parsed.get("evidence")):
        if isinstance(ev_src, str):
            fallback_evidence = ev_src
            break

    normalized: dict[str, Any] = {}
    for dim in dims:
        val = candidate.get(dim)
        if isinstance(val, dict):
            score = val.get("score")
            if isinstance(score, (int, float)):
                evidence = val.get("evidence", fallback_evidence)
                normalized[dim] = {
                    "score": float(score),
                    "evidence": evidence if isinstance(evidence, str) else str(evidence),
                }
        elif isinstance(val, (int, float)):
            normalized[dim] = {"score": float(val), "evidence": fallback_evidence}

    return normalized or None


def _run_once(
    sandbox: Path,
    judge_prompt: str,
    schema: dict,
    agent_cmd: str,
    model: str,
    timeout_s: int,
    log_dir: str | None = None,
) -> dict[str, Any] | None:
    """跑一次 agent 子进程，返回解析后的裁决 dict；任何失败返回 None（不抛异常）。

    log_dir 给定时（通常来自调用方传入的 VERIFIER_JUDGE_LOG_DIR 环境变量值），
    把这次调用的完整 stream-json 轨迹落盘（见 `_persist_trajectory`）；不给则
    完全不落盘，零额外开销。
    """
    spec_path = _write_spec_file(sandbox, judge_prompt, schema)
    result_path = sandbox / "_judge_result.json"
    if result_path.exists():
        result_path.unlink()

    evidence_desc = _describe_available_evidence(sandbox)
    prompt = (
        "你是一个证据裁判。当前目录是唯一允许读取的范围，绝不访问当前目录之外的任何路径。"
        f"证据来源：{evidence_desc}。"
        f"读取 {spec_path.name} 里的 instructions 与 output_schema。"
        "结合实际存在的证据文件自主查找与 instructions 相关的内容作为依据，"
        f"把裁决严格按 output_schema 写入 {result_path.name}。"
        "输出必须是扁平 JSON：顶层 key 直接是维度名本身（例如 has_specific_number），"
        "不要再包 dimensions、output_schema 或其它外壳。"
        "每个维度的值必须是对象，形如 {\"score\": <0~1 数值>, \"evidence\": \"...\"}。"
        "（纯 JSON，utf-8 编码，不要用 markdown 代码围栏包裹）。"
        "每个维度必须给出 evidence 字段（引用具体文件路径/轨迹行号与摘录）；"
        "找不到证据时该维度给 0 分并在 evidence 里写 'no_evidence'。"
    )
    proc = None
    timed_out = False
    try:
        proc = subprocess.run(
            [agent_cmd, "-p", "--force", "--trust", "--model", model,
             "--output-format", "stream-json", prompt],
            cwd=str(sandbox),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        proc = None
        timed_out = True
    except (FileNotFoundError, OSError):
        proc = None
    finally:
        if log_dir and proc is not None:
            _persist_trajectory(log_dir, proc)

    # 门禁：正常结束但 returncode!=0（CLI 自己报告了失败）→ 拒绝，即使文件存在；
    # FileNotFoundError/OSError（agent_cmd 不存在等根本性环境问题）→ 拒绝，即使沙箱里
    # 碰巧留有格式正确的结果文件；仅 TimeoutExpired 是例外——子进程可能在被杀前已经
    # 完整写完结果，此时若文件存在且可解析，才采信，否则仍按 None 处理。
    if proc is not None and proc.returncode != 0:
        return None
    if proc is None and not timed_out:
        return None
    if not result_path.exists():
        return None
    try:
        raw = result_path.read_text(encoding="utf-8", errors="replace")
        parsed = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return None
    return _normalize_parsed_result(parsed, schema)


def _majority_vote(samples: list[dict[str, Any]], schema: dict) -> tuple[dict[str, Any], float]:
    """对 k 次采样逐维度取中位数，返回 (聚合结果, 整体一致度 0-1)。

    一致度定义：每个维度里，与该维度中位数差距 <=0.15 的样本占比；
    再对所有维度的一致度取平均，得到整体 agreement。
    """
    dims = list(schema.get("dimensions", {}).keys())
    agg: dict[str, Any] = {}
    dim_agreements: list[float] = []

    for dim in dims:
        vals = [
            s[dim]["score"] for s in samples
            if isinstance(s.get(dim), dict) and isinstance(s[dim].get("score"), (int, float))
        ]
        if not vals:
            agg[dim] = {"score": 0.0, "evidence": "no_sample", "confidence": 0.0}
            dim_agreements.append(0.0)
            continue
        vals_sorted = sorted(vals)
        median = vals_sorted[len(vals_sorted) // 2]
        close = sum(1 for v in vals if abs(v - median) <= 0.15)
        dim_agreement = close / len(vals)
        evidences = [
            s[dim].get("evidence", "") for s in samples
            if isinstance(s.get(dim), dict) and s[dim].get("evidence")
        ]
        agg[dim] = {
            "score": median,
            "evidence": evidences[0] if evidences else "",
            "confidence": dim_agreement,
        }
        dim_agreements.append(dim_agreement)

    overall = sum(dim_agreements) / len(dim_agreements) if dim_agreements else 0.0
    return agg, overall


def invoke_agentic_judge(
    judge_prompt: str,
    schema: dict,
    workspace_path: str | None = None,
    transcript: Any = None,
    k: int = DEFAULT_K,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    agent_cmd: str = DEFAULT_AGENT_CMD,
    model: str = DEFAULT_MODEL,
    min_agreement: float = DEFAULT_MIN_AGREEMENT,
) -> dict[str, Any]:
    """唯一对外入口。永不抛异常——任何失败都归一化成 available=False。

    workspace_path 与 transcript 至少提供一个（可以两者都给，比如既要看最终产物、
    又要看执行过程中是否出现了不该做的操作）。

    k 次采样**并行**跑，各自独立沙箱、互不干扰。整体墙钟时间上界约等于单个
    timeout_s（加少量并行开销余量），不是 k 倍——外层调用方（如 run_grader.py
    的看门狗）按"单次 timeout_s + 余量"设置超时即可。

    返回：
    {
      "available": bool,             # 本次调用是否产出可信裁决（k 次采样一致度达标）
      "dimensions": {dim: {"score": float, "evidence": str, "confidence": float}},
      "agreement": float,            # k 次采样的整体一致度
      "n_samples_ok": int,           # 成功解析的采样数（<=k）
      "wall_time_s": float,
    }

    调用方约定：available=False 时，所有维度视为不可用（不得当作 0 分强行计入总分，
    应在 grader.py 里把该情况标注为 judge_unavailable，score 用其它可用信号兜底）。
    """
    if workspace_path is None and transcript is None:
        return {"available": False, "dimensions": {}, "agreement": 0.0,
                "n_samples_ok": 0, "wall_time_s": 0.0}

    t0 = time.time()
    n = max(1, k)
    # 读环境变量必须在函数体内、调用时刻读（不能当函数默认参数值缓存在模块加载时刻），
    # 因为调用方（如 evaluate_bench.py）可能在每个 (task, candidate) 观测之前动态设置
    # 这个环境变量指向不同的子目录，好让落盘的轨迹按观测分开存放。
    log_dir = os.environ.get("VERIFIER_JUDGE_LOG_DIR")
    sandboxes = [_build_sandbox(workspace_path=workspace_path, transcript=transcript) for _ in range(n)]
    try:
        samples: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=n) as pool:
            futures = [
                pool.submit(_run_once, sb, judge_prompt, schema, agent_cmd, model, timeout_s, log_dir)
                for sb in sandboxes
            ]
            try:
                for fut in as_completed(futures, timeout=timeout_s + 30):
                    sample = fut.result()
                    if sample is not None:
                        samples.append(sample)
            except FuturesTimeoutError:
                pass  # 部分样本没能在余量时间内完成；用已收集到的样本继续走投票逻辑

        if not samples:
            return {
                "available": False, "dimensions": {}, "agreement": 0.0,
                "n_samples_ok": 0, "wall_time_s": time.time() - t0,
            }

        aggregated, agreement = _majority_vote(samples, schema)
        available = agreement >= min_agreement
        return {
            "available": available,
            "dimensions": aggregated,
            "agreement": agreement,
            "n_samples_ok": len(samples),
            "wall_time_s": time.time() - t0,
        }
    finally:
        for sb in sandboxes:
            shutil.rmtree(sb, ignore_errors=True)
