# Domain Verifier 参考指南：automation-platform/agent-config

> **domain_id**: `automation-platform/agent-config`  
> **category**: Code  
> **gate_policy**: strict  
> **last_updated**: 260630_composer25_baseline

---

## 1. 任务特征

此 domain 覆盖：在 OpenClaw / ClaHub 等自动化平台上创建或修改 agent skill 配置文件（`SKILL.md` + 可选的 `cron.yaml` / `channel.yaml`），字段包括 `name`, `description`, `channel`, `target-user`, `trigger` 等。

**典型 task prompt 信号**：
- "为 XXX 创建一个 Skill"
- "配置 clawhub / OpenClaw agent"
- "设置 cron 任务 / channel 路由"

---

## 2. 必检谓词（must-have）

| 谓词 | 检查方式 | 反例-fail |
|---|---|---|
| P_skill_md_exists | 文件系统检查 `workspace/SKILL.md` | 文件缺失 |
| P_frontmatter_valid | 解析 YAML frontmatter，验证 `name` 与 `description` 字段非空 | frontmatter 缺失或 name="" |
| P_channel_correct | 从 task 规格派生期望 channel 值，与 `SKILL.md` 中 `channel:` 字段精确比对 | channel 值错误 |
| P_no_forbidden_ops | transcript 中无高危系统调用（若 task 有此约束） | agent 写了 `rm -rf` |

**Gate**：strict（所有 must-have signal ≥ 0.99 才 PASS）

---

## 3. 规则 17 应用：Fixture 真值优先对照

`P_channel_correct` 的正确写法——先从 task 规格文件（`task_md.md` frontmatter 或 inputs/）读期望 channel，再与产物比对：

```python
def _check_channel_correct(workspace_path, task_spec):
    """
    1.0 - channel 字段与 task_spec 中要求的值精确匹配
    0.5 - channel 字段存在但值模糊匹配（or-guard）
    0.0 - 字段缺失或明显错误
    # truth-source=task-spec-fixture
    # or-guard: partial → 0.5
    """
    expected_channel = task_spec.get("required_channel")  # 从 fixture 读，不硬编码
    if not expected_channel:
        return 0.5   # fixture 不可用时降级为 0.5，不单独阻断 gate
    skill_path = Path(workspace_path) / "SKILL.md"
    if not skill_path.exists():
        return 0.0
    content = skill_path.read_text(errors="replace")
    fm = _parse_frontmatter(content)
    actual_channel = fm.get("channel", "")
    if actual_channel == expected_channel:
        return 1.0
    if expected_channel.lower() in actual_channel.lower():
        return 0.5   # or-guard
    return 0.0
```

**反例**（不要这样写）：
```python
# ✗ BAD: 直接检查 "channel" 关键词出现在文件中，未比对期望值
def _check_channel(content):
    return 1.0 if "channel:" in content else 0.0
```

---

## 4. 已知陷阱

- **陷阱 1**：只检查 `SKILL.md` 存在性，不验证内容（规则 09：禁止纯存在性/子串单独满分）  
  → 修复：必须解析 frontmatter 验证关键字段

- **陷阱 2**：用 `if "clawhub" in content` 判断平台正确性  
  → 修复：从 task spec 读期望平台名，精确对比

- **陷阱 3**：cron 表达式只检查格式（`\d{1,2} \d{1,2} ...`），不验证语义值  
  → 修复：若 task spec 规定了具体频率，须对比期望 cron 字符串

---

## 5. 迭代记录

| 版本 | 实验 | 改动摘要 |
|---|---|---|
| v1 | 260625 iter_1 | 初始发现，`cold_rounds=1` |
| v2 | 260630_composer25 baseline | 扩充 guide 格式；增加 P_channel_correct 示例 |

---

## 6. 分层归属

本 domain 的全部必检谓词均可结构校验（文件存在性、frontmatter 字段值、cron 语法），`layer_hint=mostly-deterministic`，`agentic_judge_dimensions` 为空——不需要为本 domain 引入 agentic_judge 调用。若未来该 domain 出现主观维度（如"skill description 措辞是否清晰"），须先按 SKILL.md 的谓词分诊步骤判定其确实不可结构校验，再追加到 `agentic_judge_dimensions`，不得默认加入。
