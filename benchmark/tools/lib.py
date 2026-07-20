"""共享 helper：task md 解析 / 剥离 / framework 跑分加载 / workspace 构建。
无副作用（除 build_eval_workspace 写临时目录），其它纯函数。"""
from __future__ import annotations
import fnmatch
import json
import re
import shutil
from pathlib import Path

from benchmark.tools import paths

# ---- task md 定位（移植自 evaluate.py，改用 paths）----

def resolve_task_md(task_id: str) -> Path | None:
    for cand in [paths.TASKS_DIR / f"task_{task_id}.md", paths.TASKS_DIR / f"{task_id}.md"]:
        if cand.exists():
            return cand
    # 新数据 task md 命名为 T###_claweval_<id>.md（非 task_*.md），靠 frontmatter id: 匹配
    for p in paths.TASKS_DIR.glob("*.md"):
        head = p.read_text(errors="ignore")[:600]
        mm = re.search(r"^id:\s*(\S+)", head, re.M)
        if mm and mm.group(1) == task_id:
            return p
    return None


# ---- 剥离：评分侧段 + 评分侧 frontmatter 字段 ----

_SCORING_SECTIONS = {
    "automated_checks": r"## Automated Checks",
    "grading_criteria": r"## Grading Criteria",
    "llm_judge_rubric": r"## LLM Judge Rubric",
    "expected_behavior": r"## Expected Behavior",
}
_SCORING_FM_FIELDS = ["grading_type", "grading_weights", "grading"]


def strip_task_md(md_text: str) -> tuple[str, dict[str, str | None]]:
    """返回 (剥离后的 task_md 文本, 被剥离段落 dict)。

    剥离：## Automated Checks / ## Grading Criteria / ## LLM Judge Rubric /
          ## Expected Behavior，以及 frontmatter 的 grading_type/grading_weights/grading。
    保留：## Prompt 与环境 frontmatter（workspace_files/input_modality/...）。
    """
    sections: dict[str, str | None] = {k: None for k in _SCORING_SECTIONS}

    # 1) 抽出每个评分侧段的正文（含代码块），再从文本里删掉整段
    text = md_text
    for key, header in _SCORING_SECTIONS.items():
        m = re.search(rf"\n{header}\s*\n(.*?)(?=\n## |\Z)", text, re.S)
        if m:
            sections[key] = m.group(1).strip()
        text = re.sub(rf"\n{header}\s*\n.*?(?=\n## |\Z)", "\n", text, flags=re.S)

    # automated_checks 捕获到的是 ```python ... ``` 代码块；剥掉围栏得到纯 Python 源
    if sections.get("automated_checks"):
        _fence = re.search(r"```(?:python)?\s*\n(.*?)\n```", sections["automated_checks"], re.S)
        if _fence:
            sections["automated_checks"] = _fence.group(1)

    # 2) 删 frontmatter 里的评分侧字段（含其缩进子行）
    def _strip_fm_field(block: str) -> str:
        out_lines, skipping = [], False
        for line in block.splitlines():
            if line.lstrip().startswith("#"):
                out_lines.append(line)   # YAML 注释不受 skipping 影响
                continue
            key_m = re.match(r"^([a-zA-Z_]+):", line)
            if key_m:
                skipping = key_m.group(1) in _SCORING_FM_FIELDS
            if skipping:
                continue
            out_lines.append(line)
        return "\n".join(out_lines)

    fm = re.search(r"^---\n(.*?)\n---", text, re.S)
    if fm:
        new_block = _strip_fm_field(fm.group(1))
        text = text[:fm.start(1)] + new_block + text[fm.end(1):]

    text = _filter_gt_from_workspace_files(text)

    return text.strip() + "\n", sections


def _filter_gt_from_workspace_files(text: str) -> str:
    """从 frontmatter workspace_files: 块删掉 source/dest 命中 GT 的条目，防止 GT 路径名泄漏进 author 输入。"""
    fm = re.search(r"^---\n(.*?)\n---", text, re.S)
    if not fm:
        return text
    block = fm.group(1)
    lines = block.splitlines()
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        if re.match(r"^workspace_files:\s*$", line):
            out.append(line)
            i += 1
            while i < n and not re.match(r"^[A-Za-z_]\w*:", lines[i]):
                item = [lines[i]]
                i += 1
                while i < n and not re.match(r"^\s*-\s", lines[i]) and not re.match(r"^[A-Za-z_]\w*:", lines[i]):
                    item.append(lines[i]); i += 1
                vals = re.findall(r"(?:source|dest):\s*(\S+)", "\n".join(item))
                if any(is_gt_path(Path(v)) for v in vals):
                    continue   # 丢弃 GT 条目
                out.extend(item)
        else:
            out.append(line)
            i += 1
    new_block = "\n".join(out)
    return text[:fm.start(1)] + new_block + text[fm.end(1):]


# ---- workspace_files manifest 解析（移植自 evaluate.py）----

def parse_workspace_files(md_text: str) -> list[dict]:
    fm = re.search(r"^---\n(.*?)\n---", md_text, re.S)
    if not fm:
        return []
    items: list[dict] = []
    # 找所有 workspace_files: 块（frontmatter 可能含多个，例如注入检测场景）
    for m in re.finditer(r"^workspace_files:\s*\n(.*?)(?=\n[a-zA-Z_]+:|\Z)", fm.group(1), re.S | re.M):
        cur: dict = {}
        for line in m.group(1).splitlines():
            s = line.strip()
            if s.startswith("- "):
                if cur:
                    items.append(cur); cur = {}
                kv = s[2:]
                if ":" in kv:
                    k, v = kv.split(":", 1); cur[k.strip()] = v.strip()
            elif ":" in s:
                k, v = s.split(":", 1); cur[k.strip()] = v.strip()
        if cur:
            items.append(cur)
    return items


def resolve_workspace_file_source(source: str, task_id: str) -> Path | None:
    # 新数据 source 形如 "assets/T###_claweval_<id>/fixtures/x.png"（相对 SRC_BENCH，自带 assets/ 前缀）；
    # 旧数据 source 形如 "fixtures/x.png"（相对 ASSETS_DIR 或 ASSETS_DIR/task_id）。
    for c in [paths.SRC_BENCH / source, paths.ASSETS_DIR / source, paths.ASSETS_DIR / task_id / source]:
        if c.exists():
            return c
    return None


# ---- framework 跑分加载（移植自 evaluate.py，key 改为 candidate key）----

_RESULTS_CACHE: dict[str, dict[str, dict]] = {}


def load_framework_results() -> dict[str, dict[str, dict]]:
    if _RESULTS_CACHE:
        return _RESULTS_CACHE
    tmp: dict[str, dict[str, dict]] = {}
    for key, base in paths.FRAMEWORK_BASES.items():
        m = next(base.glob("*.json"), None)
        tmp[key] = {} if not m else {
            r["task_id"]: r for r in json.loads(m.read_text()).get("results", [])
        }
    _RESULTS_CACHE.update(tmp)
    return _RESULTS_CACHE


def framework_result(task_id: str, cand_key: str) -> dict | None:
    return load_framework_results().get(cand_key, {}).get(task_id)


# ---- runtime noise 过滤（移植自 evaluate.py）----

NOISE_NAMES = {
    "AGENTS.md", "BOOTSTRAP.md", "SOUL.md", "IDENTITY.md", "USER.md", "TOOLS.md",
    "HEARTBEAT.md", "HEAD", "config", "description", "exclude", "workspace-state.json",
    "agent.json", "chats.json", "chroma.sqlite3", "jobs.json", "memory_file_metadata.json",
    "MEMORY.md", "PROFILE.md", "skill.json", ".reme_store_v1", ".skill.json.lock",
}
NOISE_PREFIXES = ("pawbench-", "default_openjudge_")
NOISE_DIR_NAMES = {".git", ".openclaw", "sessions", "dialog", "embedding_cache",
                   "file_store", "media", "memory", "skills", "tool_result"}


def is_runtime_noise(name: str) -> bool:
    if name in NOISE_NAMES or name.endswith(".sample"):
        return True
    return any(name.startswith(p) for p in NOISE_PREFIXES)


def _inside_noise_dir(parts: tuple[str, ...]) -> bool:
    return any(seg in NOISE_DIR_NAMES for seg in parts)


# ---- GT 隔离判定（宪法 C3/C17）----

def is_gt_path(rel: Path) -> bool:
    for part in rel.parts:
        for pat in paths.GT_PATTERNS:
            if fnmatch.fnmatch(part, pat):
                return True
    return False


# ---- 单 candidate workspace 构建 ----

def copy_baseline_files(task_id: str, md_text: str, dst: Path, keep_gt: bool) -> None:
    """按 workspace_files manifest 从 assets stage baseline 文件到 dst。keep_gt=False 时跳过 GT 文件。"""
    for item in parse_workspace_files(md_text):
        src = resolve_workspace_file_source(item.get("source", ""), task_id)
        dest_rel = item.get("dest", "")
        if not src or not dest_rel:
            continue
        if not keep_gt and is_gt_path(Path(dest_rel)):
            continue
        dp = dst / dest_rel
        dp.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy(src, dp)
        elif src.is_dir():
            shutil.copytree(src, dp, dirs_exist_ok=True)


def build_one_workspace(task_id: str, cand_key: str, dst: Path, keep_gt: bool) -> bool:
    """把一个 candidate 的 end-state workspace 物化到 dst。
    keep_gt=False：隔离 GT（给 verifier_author_inputs）；True：保留 GT（给有效性校验临时用）。
    返回 False 表示该 candidate 没跑这个 task。
    注：baseline 文件 staging 失败会抛异常（视为致命，输入环境不完整）；agent overlay 单文件拷贝失败是 best-effort 静默跳过。
    """
    base = paths.FRAMEWORK_BASES[cand_key]
    src_ws = base / "workspaces" / task_id
    if not src_ws.exists():
        return False
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    md = resolve_task_md(task_id)
    if md:
        copy_baseline_files(task_id, md.read_text(), dst, keep_gt)
    # 2) overlay agent workspace（去 noise，按需去 gt）
    for p in src_ws.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(src_ws)
        if _inside_noise_dir(rel.parts) or is_runtime_noise(rel.name):
            continue
        if not keep_gt and is_gt_path(rel):
            continue
        tgt = dst / rel
        tgt.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy(p, tgt)
        except Exception:
            pass
    return True
