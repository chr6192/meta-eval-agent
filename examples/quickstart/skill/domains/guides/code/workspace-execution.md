# Domain Verifier 参考指南：code/workspace-execution

> **domain_id**: `code/workspace-execution`
> **category**: Code
> **gate_policy**: strict
> **layer_hint**: mostly-deterministic
> **last_updated**: 260701_agenticjudge_relocate

---

## 1. 任务特征

Prompt 要求产出可运行脚本、shell 命令、或可执行工作流，需要真的跑起来验证行为是否正确。

---

## 2. 核心原则

执行验证必须在传入的候选 `workspace_path` 上运行，**禁止**在 grader 内部自建临时目录、伪造一套测试场景后在那套假场景上运行。期望结果须从 workspace 输入文件动态推导，不得硬编码。

---

## 3. 反例（自建假测试环境，会导致判分与候选实际产物完全无关）

```python
# ✗ 错误模式：grader 自建临时目录冒充 workspace
def _executable_behavior_signal(command_text, workspace_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        _build_fake_scene(Path(tmpdir))       # ← grader 在 tmpdir 自造一套文件树
        result = subprocess.run(
            ["sh", "-c", command_text],
            cwd=tmpdir,                        # ← 在自造的假场景上运行，与候选真实 workspace 无关
            capture_output=True, timeout=30,
        )
        got = set(_parse_output_paths(result.stdout.decode()))
        expected = _reference_matches(Path(tmpdir))  # ← 期望也是在假场景上算的
        return 1.0 if got == expected else 0.0
# 问题：候选的 command 在这套自造场景上跑通，不代表它在候选真实 workspace 上是正确的
```

---

## 4. 正例（在真实 workspace_path 上派生期望并执行）

```python
# ✓ 正确模式：从 workspace 输入派生期望，在候选真实 workspace_path 执行
def _executable_behavior_signal(command_text, workspace_path):
    """
    1.0 - command 在候选 workspace 执行，输出路径集与 workspace 内容派生的期望精确匹配
    0.5 - command 可执行但输出集与期望有偏差
    0.0 - 执行失败或无输出
    """
    expected = _derive_expected_from_workspace_inputs(workspace_path)
    if expected is None:
        return 0.5   # fixture 不可用时降级，不直接判 0

    result = subprocess.run(
        ["sh", "-c", command_text],
        cwd=workspace_path,             # ← 在候选实际 workspace 上运行，不是临时目录
        capture_output=True, timeout=30,
    )
    if result.returncode != 0:
        return 0.0

    got = set(_parse_output_paths(result.stdout.decode()))
    if got == expected:
        return 1.0
    if got & expected:
        return 0.5
    return 0.0


def _derive_expected_from_workspace_inputs(workspace_path):
    """从 workspace 输入（task 规格里描述的对象）推导期望输出，不是 grader 内嵌的硬编码值。"""
    root = Path(workspace_path)
    if not root.is_dir():
        return None
    matches = set()
    for f in root.rglob("*.log"):
        try:
            if "FATAL:" in f.read_text(errors="replace"):
                matches.add(str(f.relative_to(root)))
        except OSError:
            pass
    return matches if matches else None
```

---

## 5. 迭代记录

| 版本 | 实验 | 改动摘要 |
|---|---|---|
| v1 | 260625 | 首次发现自建假场景问题 |
| v2 | 260701_agenticjudge | 从统一规则文档下放为独立 domain guide |
