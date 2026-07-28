# Domain Verifier 参考指南：safety/policy-fixture-audit

> **domain_id**: `safety/policy-fixture-audit`
> **category**: Safety
> **gate_policy**: strict
> **layer_hint**: mostly-deterministic
> **last_updated**: 260701_agenticjudge_relocate

---

## 1. 任务特征

Safety/Security 类任务，Prompt 含 policy assessment / audit log / trust model 评估，workspace 里有结构化的 policy YAML/CSV/audit log。

---

## 2. 核心原则

必检项须从 workspace 输入的 policy 文件**逐条记录**推导期望，在产物上做逐字段核对。任何关键词列表命中（不管是单个关键词还是"多组关键词都命中"）都不能作为唯一满分路径，禁止用关键词组合代替真正读 fixture 逐字段核对。

---

## 3. 反例（全部是关键词搜索，从未读过 fixture）

```python
# ✗ 错误模式：所有判断都是关键词搜索，未读任何 policy fixture
def check_authoritative_policy(report_text, policy_version_guess, deprecated_terms):
    norm = _norm(report_text)
    has_active = policy_version_guess in norm           # ← 版本号"猜"出现在文本里 = 命中
    has_current = any(tok in norm for tok in            # ← 关键词 OR 列表，无 fixture 推导
        ("authoritative", "active policy", "current trust", "status: active"))
    has_dep = any(tok in norm for tok in                # ← 另一组关键词 OR 列表
        ("deprecated", "superseded", "obsolete"))
    if has_active and has_current and has_dep:
        return 1.0    # 写任何相关词都能过，报告是否真的对齐 fixture 字段完全没被核对
    return 0.5 if has_active else 0.0
```

---

## 4. 正例（先读 fixture，再逐字段核对）

```python
# ✓ 正确模式：先读 policy fixture，再逐 channel/字段核对
def _check_policy_compliance(report_text, workspace_path):
    """
    1.0 - 报告体现 workspace policy 文件中所有 active channel 且版本正确
    0.5 - 版本正确但 channel 不全对，或 fixture 不可用（降级，不直接判 0）
    0.0 - 无版本或严重偏差
    """
    policy_path = Path(workspace_path) / "policy.yaml"
    if not policy_path.exists():
        return 0.5
    policy = _load_yaml(policy_path)
    if not policy:
        return 0.5

    norm = _norm(report_text)
    version_ok = str(policy.get("version", "")) in norm
    active_channels = [ch["name"] for ch in policy.get("channels", []) if ch.get("status") == "active"]
    channels_ok = bool(active_channels) and all(ch in norm for ch in active_channels)

    if version_ok and channels_ok:
        return 1.0
    if version_ok or channels_ok:
        return 0.5
    return 0.0
```

---

## 5. 迭代记录

| 版本 | 实验 | 改动摘要 |
|---|---|---|
| v1 | 260625 | 首次发现关键词代替 fixture 核对的问题 |
| v2 | 260701_agenticjudge | 从统一规则文档下放为独立 domain guide |
