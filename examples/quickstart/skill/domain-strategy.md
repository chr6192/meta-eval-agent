# Step 0 · Domain 识别与路由（verifier-author 子文件）

> 在 Step 1（分解任务）**之前**执行。本文件由 SKILL.md 引用。

---

## 设计意图

Domain 系统的目的是**在多次实验迭代中，累计积累出各 domain 下有效的 verifier 构建参考**，供 verifier-author 复用，减少从零摸索的成本。

- `domains/registry.json`：所有已知 domain 的索引（id、关键词、gate_policy、guide 路径）
- `domains/guides/{domain_id}.md`：每个 domain 的 verifier 构建参考指南（含典型谓词、EX 应用方式、已知陷阱）

**operator（skill-optimizer）负责 CRUD**：每轮审计后，optimizer 根据 auditor 发现的模式，增删改 registry 条目和 guide 文件（见本文件 §4）。verifier-author 是**只读消费者**，不写 discovered 记录。

---

## Step 0-1 · 关键词匹配

读取当前 task 的 `verifier_author_inputs/task_md.md`（frontmatter + `## Prompt` 部分）。

对照 `skill/domains/registry.json`：逐条比对 `keywords` 字段，任意关键词出现在 task 文本中（大小写无关）则视为命中。

输出：
- 命中：`matched_domain = [<domain_id>, ...]`（可以是列表），`guide_paths = [<domains/guides/...>, ...]`
- 未命中：`matched_domain = []`

> **多个 domain 同时命中时全部读，不要只挑一个**——每份 guide 覆盖不同的具体谓词类型，通常并不互斥。若多份 guide 对同一条谓词的 `gate_policy`/`layer_hint` 冲突，以 `meta-rules.md` 规则 15 为准裁决。

---

## Step 0-2 · 命中 → 读取 domain 指南

```bash
# 命中时，在沙箱内读取**全部**命中的 guide（不要只读一条）：
cat skill/domains/guides/<domain_id>.md   # 对 matched_domain 里的每个 domain_id 重复
```

将 guide 中的内容带入 Step 1–3：

| Guide 字段 | 用途 |
|---|---|
| `gate_policy` | Step 2 选闸门公式的先验（仍受规则 15 可结构校验优先约束） |
| `layer_hint` | Step 1.1 谓词分诊的先验参考（`mostly-deterministic`/`mixed`/`mostly-agentic-judge`）——不是强制结论，仍需逐条按 Q1-Q3 验证 |
| `deterministic_predicates` | Step 1 画 atomic_predicates 的推荐检查维度 |
| `agentic_judge_dimensions` | Step 1.1 标为 agentic_judge 时，`judge_prompt`/schema 撰写的起点参考 |
| 已知陷阱 | Step 3 自我反思的重点自检项 |
| 正例/反例代码 | Step 2 编码时的模式参考——领域专属规则（如 Code 的执行验证、Security 的逐记录核对）的**完整正文只存在于对应 guide**，不在 `meta-rules.md` 里重复，命中该 domain 时必须完整读 |

> domain 指南是**先验提示**，不替代 Step 1–3 的 self-reflection；与 `meta-rules.md` 冲突时以 `meta-rules.md` 为准。

---

## Step 0-3 · 未命中 → 按 Step 1.1 分诊

未命中任何 domain 时，不套用任何 domain 表格，按 `SKILL.md` Step 1.1 的谓词分诊流程（Q1–Q3）从头判断，照常进入 Step 1。

---

## Step 0-4 · Step 3 结束后输出 domain note

在 Step 3 self-reflection 收敛后，在 `output/verifier_summary.md` 末尾追加一个简短的 domain note（**不写文件到 domains/，只追加到 summary**）：

```markdown
## Domain Note
- matched_domain: [<domain_id>, ...]（可以是列表；未命中时写 `[]`；多命中时如实列全部，不要只报一个）
- inferred_domain: <若未命中，推断的 domain 层级名，如 office/financial-report；若已命中则写 null>
- key_pitfalls_hit: [<Step 3 自检中发现的、命中 domain guide `known_pitfalls` 的具体反例模式，供 optimizer 参考>]
- guide_useful: <yes/no/n-a>（命中时填：guide 的已知陷阱是否实际命中）
```

这些 note 由 **verifier-auditor** 收集，由 **skill-optimizer** 决定是否新增/修订 domain 条目（见 §4）。

---

## §4 · optimizer 的 CRUD 职责（每轮迭代）

> 本节供 skill-optimizer 参考，verifier-author 不需要执行。

### 新增 domain（CREATE）

当 auditor 发现某类 task 中 inferred_domain 反复出现（≥3 个 task 均推断出同一 domain 名），且已有明显的 verifier 构建模式可复用时，optimizer 执行：

1. 在 `domains/registry.json` 追加条目：

```json
{
  "domain_id": "<层级名，如 office/financial-report>",
  "category": "<Code|Office|Safety|Multimodal|Creative|...>",
  "description": "...",
  "keywords": ["...", "..."],
  "gate_policy": "strict|strict-if-checkable",
  "layer_hint": "mostly-deterministic|mixed|mostly-agentic-judge",
  "deterministic_predicates": ["..."],
  "agentic_judge_dimensions": [
    {"dimension": "...", "judge_question": "..."}
  ],
  "anchor_hints": ["..."],
  "known_pitfalls": ["..."],
  "verifier_guide": "guides/<domain_id>.md",
  "discovered_in": "<实验 id>",
  "last_updated": "<实验_iter_N>",
  "deprecated": false
}
```

> `gate_policy` 目前 registry.json 里只出现过 `strict`（可结构校验优先）和 `strict-if-checkable`（含 agentic_judge 维度、按可核对程度收紧），没有 `lenient` 取值。`layer_hint` 为空 `agentic_judge_dimensions` 数组时通常配 `mostly-deterministic`。

2. 创建 `domains/guides/<domain_id>.md`（参照已有 guide 格式）。

### 更新 domain（UPDATE）

当某个已有 domain 的 guide 被证明不够精准（同 domain 的 task 仍有高比例 false-pass / false-fail），optimizer 修订：
- 更新 `registry.json` 对应条目的 `known_pitfalls`、`anchor_hints`、`gate_policy`
- 修订 guide 文件对应章节，标注版本注（如 `v2 · 260630_composer25_iter_3 修订`）
- 更新 `last_updated` 字段

### 冻结/弃用 domain（SOFT DELETE）

当某 domain 连续 3 轮指南未被命中且未贡献改善时，可设 `"deprecated": true`（不物理删除），verifier-author 命中 deprecated domain 时跳过 guide 加载。

### 强化已有 domain

auditor 发现 guide 中漏了某类陷阱时，optimizer 在 guide §4 "已知陷阱" 追加条目，并在 §5 "迭代记录" 中注明。

---

## 文件结构

```
skills/verifier-author/domains/
├── registry.json            # domain 索引（optimizer CRUD）
└── guides/                  # per-domain verifier 构建参考（optimizer CRUD）
    ├── automation-platform/
    │   └── agent-config.md
    ├── office/
    │   └── financial-report.md   # (由 optimizer 在发现模式后创建)
    └── ...
```
