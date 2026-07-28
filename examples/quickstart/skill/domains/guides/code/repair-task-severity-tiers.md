# Domain Verifier 参考指南：code/repair-task-severity-tiers

> **domain_id**: `code/repair-task-severity-tiers`
> **category**: Code
> **gate_policy**: strict
> **layer_hint**: mostly-deterministic
> **last_updated**: 260701_agenticjudge_relocate

---

## 1. 任务特征

Code/Engineering 类的修复/补全/配置对齐任务：把候选产物与一份 fixture（期望配置/期望代码状态）做比对。

---

## 2. 核心原则（防止"略差即全 FAIL"的错杀）

把必检字段拆成两级：
- **核心不变量**（core）：缺了就是真的错，判 0 分。
- **次要字段**（secondary）：默认只是加分项；如果确实要作为必检项，必须在 `verifier_summary.md` 写明理由，且缺了只打对折（0.5），不因为这一项单独拖垮整体闸门（前提是其它核心项都满足）。

权限/属主/文档这三类检查尤其容易过严：只有 Prompt 明确要求某种严格形态（如"owner-only"）时才按严格标准判 0 分；没有明确要求时，部分符合给 0.5，不要求候选猜中一个 Prompt 没说的严格标准。

---

## 3. 代码示例

```python
def _grade_repair_task(workspace_path, fixture):
    core_signals = {
        "syntax_valid": _check_syntax(workspace_path),          # 缺了就是错：0.0
        "core_logic_fixed": _check_core_bug_fixed(workspace_path, fixture),
    }
    secondary_signals = {
        "docstring_updated": _check_docstring(workspace_path),   # 次要：缺了 0.5，不拖垮闸门
        "permission_mode": _check_permission_mode(workspace_path, fixture),
    }
    core_pass = all(v >= 0.99 for v in core_signals.values())
    secondary_avg = sum(secondary_signals.values()) / max(1, len(secondary_signals))
    return {
        "outcome_passed": core_pass,        # 闸门只看 core
        "score": secondary_avg,
        "breakdown": {**core_signals, **secondary_signals},
    }


def _check_permission_mode(workspace_path, fixture):
    """
    1.0 - 权限模式与 fixture 完全一致
    0.5 - 权限模式部分符合（如只多了/少了非 Prompt 明确要求的严格位）
    0.0 - 权限模式与 Prompt 明确要求的严格形态相悖
    """
    required = fixture.get("required_permission_mode")
    actual = _read_permission_mode(workspace_path)
    if required is None:
        return 0.5   # Prompt 未明确要求严格形态时不判 0
    return 1.0 if actual == required else 0.0
```

---

## 4. 迭代记录

| 版本 | 实验 | 改动摘要 |
|---|---|---|
| v1 | 260625 | 首次发现"略差即全 FAIL"的错杀模式 |
| v2 | 260701_agenticjudge | 从统一规则文档下放为独立 domain guide |
