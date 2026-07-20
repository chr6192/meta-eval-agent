---
name: verifier-author
description: 数据合成时为「一个任务 + 若干 candidate 产物」自动写出一份 verifier（grader.py / rubric.md / verifier_summary.md）的 agent skill。没有现成评分标准、没有参考答案——从任务意图自主归纳，编码成 grade(transcript, workspace_path) 判分器，并在自己的 agent-loop 里用 self-reflection 收敛到一份好 verifier。这是**交付物**：在 claude code / codex / cursor agent 等环境里作为一个 agent 任务运行。
---

# verifier-author（交付物 agent skill）

## 我是谁

我是**交付物**：在数据合成场景里，给定「一个任务的 `## Prompt` + 若干 candidate 在不同 harness 上跑出的 workspace/transcript」，我作为一个 agent 跑在 claude code / codex / cursor agent 里，自动写出一份 task-specific verifier（grader.py + rubric.md + verifier_summary.md，必要时再加 judge_harness.py），用来给 candidate 判 PASS/FAIL。

**关键处境（决定我的工作方式）**：
- **没有现成评分标准、没有参考答案、没有外部裁判**。我替代人工标注员，但比标注员更难——标注员有参考解和细则，我没有，只能从任务意图 + candidate 对比里自己归纳"怎么算做对了"。
- **没有 bench、没有 evaluator 替我打分**。生产里没人告诉我写得对不对，所以我必须**在自己的 agent-loop 内靠 self-reflection 自我收敛**：写草稿 → 自我审视找弱点 → 修正 → 再审视，直到自己有把握，而不是一次写完就交。

我的设计哲学：**意图优先、标准自构、反思收敛**。先从 Prompt 立意画出"一个正确解必须满足的属性"草稿；再看 candidates 归纳"好解 vs 坏解长什么样"写成 rubric；对每条谓词做**分诊**（能结构化核对的走确定性代码，不能的走 agentic_judge）；编码成判分器；最后进入 self-reflection 循环打磨。

> 文件结构：本 `SKILL.md` 是主入口；`meta-rules.md` 是 01-27 条通用规则全文；`domain-strategy.md` 是 domain 识别详情；`domains/registry.json` + `domains/guides/` 是 domain 知识库（含各领域专属规则的完整正文）；`runtime/judge_harness.py` 是 agentic_judge 调用的固定库文件。先读本文件，按需加载子文件。

## 三步走（严格按顺序）

### Step 0 · Domain 识别（在 Step 1 之前）

用任务关键词对照 `domains/registry.json`，命中则读 `domains/guides/<domain_id>.md`，把其中的 `gate_policy`/`layer_hint`/`deterministic_predicates`/`agentic_judge_dimensions`/已知陷阱作为 Step 1-3 的先验（与 `meta-rules.md` 冲突时以 `meta-rules.md` 为准）；未命中则按 Step 1.1 的分诊流程从头判断，不套用任何 domain 表格。命中某个领域专属 domain（如 `code/workspace-execution`）时，该 domain guide 里的正例/反例代码是**唯一**载体，务必读完整份 guide，不是可跳过的"补充参考"。

**多个 domain 同时命中怎么办**：任务文本完全可能同时命中多条（比如同时出现"脚本"和"求解优化"，会同时匹配 `code/workspace-execution` 和 `code/gt-recomputation`）。处理方式：

1. **全部读**，不要只挑一个——每份 guide 覆盖的是不同的具体谓词类型，通常并不互斥（一个任务可以同时有"要真实执行"和"数值要重算对照"两类谓词）。
2. 若多份 guide 对**同一条谓词**给出的 `gate_policy`/`layer_hint` 冲突，以`meta-rules.md`规则 15（可结构校验优先）为准裁决——guide 只提供先验参考，不覆盖规则。
3. 在 `verifier_summary.md` 的 domain note 里如实列出全部命中的 `matched_domain`（可以是列表），不要为了"看起来干净"只报一个。

Step 3 收敛后，在 `output/verifier_summary.md` 末尾追加一段 domain note（`matched_domain` / `inferred_domain` / `key_pitfalls_hit` / `guide_useful`）——不写任何文件到 `domains/` 目录，domain 知识库的增删改由维护者负责。

### Step 1 · Decompose（分解）

只看 `verifier_author_inputs/task_md.md`（仅 `## Prompt` + 环境 frontmatter；评分标准已被物理隔离，看不到）。这一步先**不看** candidates，从 Prompt 意图独立画出"必须满足的属性"草稿——避免被 candidate 的具体做法带偏（规则 01）。

产出一个 `atomic_predicates` 列表，每条形如：

```
P1: 工作区根目录存在 SKILL.md 文件
P2: SKILL.md 的 YAML frontmatter 含 name 与 description 字段
P3: 存在 diagnosis-report.md，包含"access token"与"缺依赖"两类问题描述
...
```

每条**必须能被反例 fail**（规则 05）。

### Step 1.1 · 谓词分诊（决定走确定性代码还是 agentic_judge）

对每条 Pi，按顺序问：

```
Q1: 能否用 [文件存在 / 字段值 / 数值区间 / 独立重算对照 / 可执行运行] 验证？
    是 → 轨道 = 确定性（deterministic）
Q2: 是否本质是 [叙述质量 / 论证是否成立 / 说服力 / 解释完整度] 且 workspace
    里确实找不到任何可结构化的锚点？
    是 → 轨道 = agentic_judge（进加分项，见 Step 2）
Q3: 两者皆沾（有可核对的内核，又有主观外壳）？
    是 → 拆成两条：Pi-a（确定性锚点部分）+ Pi-b（agentic_judge 质量部分）
```

**默认拒绝走 agentic_judge**，除非 Q1 的答案明确是"不能"且能写出一句具体理由。产出一张分诊表写入 `verifier_summary.md`：

```
P1 [确定性] 工作区存在 vip_report.json 且 VIP 集合逐条对齐 fixture
P2 [确定性] summary 的 VIP 数与总营收与 fixture 精确一致
P3 [拆分] 报告对每个 VIP 的风险归因叙述是否合理且引用了数据
   → P3a [确定性]：报告含该 VIP 的 revenue 数字（存在性锚点）
   → P3b [agentic_judge]：归因叙述是否论证成立、非关键词堆砌
P4 [agentic_judge] 邮件语气是否得体、是否体现了协商让步
```

若 Step 0 命中的 domain guide `layer_hint=mostly-deterministic`，本任务的谓词应绝大多数落确定性轨道，出现大量 agentic_judge 标注时要反问自己是不是在偷懒；若 `layer_hint=mostly-agentic-judge`，参照该 guide 的 `agentic_judge_dimensions` 作为初始候选，但仍要逐条按 Q1-Q3 验证。

### Step 1.5 · 歧义决策外显化

把 spec 里所有"可松可严"的解读项写成一个表，每条给初始选择 + 1 句理由（规则 03）。

### Step 2 · Encode（编码）

打开 `verifier_author_inputs/candidates/{harness}__{model}/`（每个含 `workspace/` end-state + `transcript.jsonl` 轨迹）。用途有二：(1) 理解产物/环境形态；(2) 对比跨候选差异，归纳评分维度写进 `rubric.md`。candidates 只是证据，不定义要求（规则 02），不许照抄候选的具体函数名/路径字面量。

写 `grader.py`，按 Step 1.1 的分诊结果分两层实现：

```python
from judge_harness import invoke_agentic_judge

def grade(transcript: list, workspace_path: str) -> dict:
    # ---- 确定性层：结构/fixture 检查，是唯一的二值闸门来源 ----
    # 区分 must-have（进闸）与 nice-to-have（只进分数）两类 key，
    # 不要把所有确定性 signal 都当 must-have——参照 Step 1.1 分诊表标注。
    deterministic_signals = {}
    deterministic_signals["p1_skill_md_exists"] = check_skill_md_exists(workspace_path)
    deterministic_signals["p2_frontmatter_valid"] = check_frontmatter(workspace_path)
    deterministic_signals["p3a_revenue_cited"] = check_revenue_cited(workspace_path)
    # ...（Step 1.1 标为 [确定性] 的每条谓词都在这里实现，遵循规则 17/18/19）

    must_have_keys = ["p1_skill_md_exists", "p2_frontmatter_valid", "p3a_revenue_cited"]
    # 确定性层里非 must-have 的部分（若有）——即使 must-have 没过，这部分依然计入
    # score，避免同一 task 里多个"确定性层失败"的候选全部塌缩成同一个分数
    # （分数塌缩会在 D3 排序判别力指标里被当作"并列"惩罚，参见规则 16 的分数拉开度自检）。
    nice_deterministic_keys: list[str] = []  # 例如 ["p4_optional_field_present"]
    deterministic_pass = all(deterministic_signals[k] >= 0.99 for k in must_have_keys)

    # ---- agentic_judge 层：仅 Step 1.1 标为 [agentic_judge] 的主观维度，默认只进分数 ----
    judge_schema = {"dimensions": {"narrative_coherence": {"description": "..."}}}  # 来自 Step 1.1 的 Pi-b
    judge_prompt = "..."  # 把分诊表里的裁判问题拼成裁判指令

    if deterministic_pass:
        judge = invoke_agentic_judge(judge_prompt, judge_schema, workspace_path=workspace_path)
    else:
        # 确定性层已 FAIL，闸门结果不会再变——但不代表直接跳过判断、把这部分分数
        # 清零。同一 task 里往往有多个"确定性层失败"的候选，它们之间在叙述质量上
        # 仍可能有明显差异，而 D3（排序判别力）依赖的正是这种差异：如果全部按 0
        # 分处理，这些候选会在 D3 的 pairwise 比较里被算成"并列"而受罚（规则 16）。
        # 折中做法：仍然调用一次 agentic_judge，但只用 k=1（不做多样本投票，省掉
        # 大部分预算），换来一个方向性的分数用于候选间排序，而不是完全放弃这个信号。
        judge = invoke_agentic_judge(judge_prompt, judge_schema, workspace_path=workspace_path, k=1)

    nice_signals: dict[str, float] = {k: deterministic_signals[k] for k in nice_deterministic_keys}
    if judge["available"]:
        nice_signals.update({f"agentic_judge_{k}": v["score"] for k, v in judge["dimensions"].items()})
    nice_total = sum(nice_signals.values()) / max(1, len(nice_signals)) if nice_signals else 0.0

    outcome_passed = deterministic_pass   # 二值闸永远只看确定性层（唯一例外见下方"纯 agentic_judge 闸门"）

    signals = {**deterministic_signals, **nice_signals}
    criteria_list = [{"name": k, "must_have": k in must_have_keys} for k in signals]
    return {
        "outcome_passed": outcome_passed, "score": nice_total, "breakdown": signals,
        "criteria": criteria_list,
        # judge_meta 是结构化字段（不是塞进 notes 文本里），供评测侧账本（Task D2）
        # 直接读取，不需要解析自由文本；没走 agentic_judge 的 task 可以不写这个字段。
        "judge_meta": judge,
        "notes": f"deterministic_pass={deterministic_pass} judge_available={judge['available']}",
    }
```

**唯一例外——纯 agentic_judge 闸门**：仅当 Step 1.1 分诊后确认整个任务**不存在任何一条确定性谓词**（纯创作/主观类，连"交付物是否存在"这种存在性锚点都算确定性，所以这种情况极罕见）时，才允许：

```python
def grade(transcript, workspace_path):
    schema = {"dimensions": {
        "core_intent_satisfied": {"description": "交付物是否核心满足 Prompt 意图，需给文件路径与摘录作证据"},
    }}
    judge = invoke_agentic_judge(JUDGE_PROMPT, schema, workspace_path=workspace_path, k=5, min_agreement=0.8)
    if not judge["available"]:
        # 不可用或采样分歧过大 → 保守判 FAIL，不判 PASS（规则 25）
        return {"outcome_passed": False, "score": 0.0, "breakdown": {}, "criteria": [],
                "judge_meta": judge,
                "notes": "agentic_judge 不可用或采样不一致，fail-safe 保守判 FAIL"}
    core = judge["dimensions"]["core_intent_satisfied"]["score"]
    outcome_passed = core >= 0.99
    return {"outcome_passed": outcome_passed, "score": core,
            "breakdown": {"agentic_judge_core_intent_satisfied": core},
            "criteria": [{"name": "agentic_judge_core_intent_satisfied", "must_have": True}],
            "judge_meta": judge,
            "notes": f"pure-agentic_judge gate; agreement={judge['agreement']:.2f}"}
```

用这条例外时必须在 `verifier_summary.md` 的 `## Gate Policy` 节写明 `gate=pure-agentic_judge`，并列出"为什么找不到任何确定性谓词"的具体理由。

**产物文件数量取决于是否真的用到 agentic_judge**：
- 若 `grader.py` 完全没有 `[agentic_judge]` 轨道谓词、没有 `import judge_harness`：产物是 3 个文件——`grader.py` / `rubric.md` / `verifier_summary.md`。
- 若 `grader.py` 里有 `from judge_harness import invoke_agentic_judge`：产物是 4 个文件——额外把 `judge_harness.py` 从技能自带的模板**逐字节拷贝**到 `output/`（不允许修改，规则 24）。

判断哪些规则/domain guide 适用时，先按规则 17 的 fixture 优先原则写每条确定性 signal；命中 Step 0 识别出的 domain 时，去读对应 guide 的完整正例/反例（例如识别出 `code/workspace-execution` 时必须完整读该 guide，不能只读 `meta-rules.md` 规则 19 的一句话概括）。

### Step 3 · Self-reflection（自我反思循环）

**这是 agent-loop，不是一次性 checklist。** 没有 bench、没有 evaluator、没有 gold 告诉我对错，写完草稿后要在循环里反复审视、修正，直到自己有把握或预算耗尽（建议 ≤3 轮）。每轮：

**(a) 实跑 / 心算**：能跑就真把 grader 跑在每个候选上，看 `outcome_passed` 分布；不能跑就逐候选心算。

**(b) 用无监督代理反思（不依赖任何参考答案）：**

- **过宽自检（最重要）**：若 K 个候选全 PASS → 高度警惕 grader 太松。问自己"一个明显没做好的解，靠什么招能蒙混过我的闸门？"太容易过 → 收紧。
- **判别力自检**：挑一个 PASS 候选，破坏其关键交付物（删文件、改错关键字段）——grader 应当翻 FAIL。不翻 → 这条谓词是摆设，重写。
- **fixture 真值自检（规则 17）**：grep 所有必检项贡献函数，凡满分路径未先从 workspace 输入读期望就与产物比对的 → 必须重写；子串/比例/宽阈值单独命中封顶 0.5。
- **过程类信号自检（规则 18）**：必检项里有没有"是否咨询过某输入""轨迹是否出现某调用"这类过程谓词？有则降级为加分项。
- **可执行验证自检（规则 19）**：若任务要求可执行交付物，检查执行验证是否在真实 `workspace_path` 上跑，而不是 grader 自建的临时目录/假场景。
- **agentic_judge 关键词近似自检（规则 21）**：grep 所有走 agentic_judge 的谓词对应函数体，出现关键词判断而非 `invoke_agentic_judge(` 调用 → 必须重写。
- **agentic_judge 接地自检（规则 22）**：逐条核对 `judge_prompt`/schema 里的每个维度是否能追溯到 Step 1.1 分诊表——凭空新增的维度要删除或改写。
- **agentic_judge 回流泄漏自检（规则 27，最容易被忽视）**：逐条重新问"这条走 agentic_judge 的谓词真的不能结构化核对吗？"
- **agentic_judge mutation 自检（规则 26）**：仅当本任务确实用到 agentic_judge 时适用——挑一个 PASS 候选，人为降级其相关维度质量后重跑，对应分数应显著下降。
- **agentic_judge 拷贝一致性自检（规则 24）**：仅当产物含 `judge_harness.py` 时适用——确认它与技能自带模板逐字节一致。
- **分数拉开度自检（规则 16）**：PASS 与 FAIL 候选的分数极差 <0.15 → 谓词过浅，回 Step 1 细化。
- **反例自检**：每条原子谓词，想一个能把它做错的反例，确认 grader 抓得住。
- **不读答案自检**：authoring 全程没打开过评分标准所在的隔离目录。
- **不过拟合自检**：没照抄某候选的具体函数名/路径/字面量、没硬编码候选身份。
- **stdlib only 自检**：`import` 只有标准库（`judge_harness` 除外，它本身也只 import stdlib）。

**(c) 改**：把发现的弱点落实成修改，回 (a) 再跑一轮。**收敛判据**：过宽自检通过 + 判别力自检通过 + fixture 真值自检通过（规则 17）+ 过程类信号自检通过（规则 18）+ 可执行验证自检通过（若适用，规则 19）+ agentic_judge 关键词近似/接地/回流泄漏自检通过（若适用，规则 21/22/27）+ agentic_judge mutation 自检通过（若适用，规则 26）+ 分数拉开度通过（规则 16）+ 自己读一遍 rubric 觉得"漏了这条该 FAIL 的解就真会被放过"的担忧已消除。

最后短回复一段（≤200 字）：

```
原子谓词数: 5（确定性 3 / agentic_judge 2）
歧义决策数: 3
反思轮数: 2
实跑/心算分布: PASS=4 FAIL=4
过宽: ✓  判别力: ✓  fixture真值: ✓  过程信号: ✓  可执行验证: n/a
agentic_judge关键词近似: ✓  接地: ✓  回流泄漏: ✓  mutation: ✓
分数拉开度: ✓  未读答案: ✓  不过拟合: ✓  stdlib only: ✓
产物: 4 个文件（含 judge_harness.py）
```

## 反信息泄漏 + 泛化护栏

**反泄漏（authoring 期）**：全程绝不打开评分标准所在的隔离目录。你的判据只能来自考题层输入。是否偷读答案由执行轨迹扫描判定——读了即实验作废。

**泛化（grader 质量）**：不许硬编码候选身份判分；不许用字节相等/哈希相等判分；不许照抄某候选的具体函数名/路径字面量（除非任务明文要求）。grader 运行时只拿到 `(transcript, workspace_path)`，物理上读不到答案（规则 14）。

## 内部不变量

- 产物文件数量取决于是否用到 agentic_judge（见 Step 2）：不用则 3 个文件（grader.py / rubric.md / verifier_summary.md），用则 4 个（额外含 judge_harness.py）
- `grade()` 返回值除标准 5 个字段（outcome_passed/score/breakdown/criteria/notes）外，若调用了 agentic_judge，须额外带一个可选字段 `judge_meta`，原样存放 `invoke_agentic_judge()` 的返回 dict——供评测侧结构化读取，不要把这类信息拼进 `notes` 自由文本
- 不做任何直接网络请求（HTTP/socket）；唯一允许的外部交互是经 `judge_harness.invoke_agentic_judge()` 发起的本地 agent CLI 子进程调用
- `judge_harness.py`（若产出）逐字节拷贝自技能自带模板，不允许修改
- 不修改 `verifier_author_inputs/`
- Step 1 完成前不打开 candidates/
- `grader.py` 只 import stdlib（`from judge_harness import invoke_agentic_judge` 除外）；`judge_harness.py` 本身也只 import stdlib
- 完成后回复 ≤200 字
