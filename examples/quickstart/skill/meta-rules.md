# verifier-author 判分规则全文（01-27）

> 本文件由 SKILL.md 按需引用。规则按两位数字编号排列，编号本身不承载语义顺序，只是稳定引用锚点；每条规则的名字本身就说明了它在管什么，不需要额外查表。

## 01. 立意先于证据 (intent-before-evidence)

先从 Prompt 独立画出"必须满足的属性"草稿，完成前**严禁打开 candidates**。理由：评分标准已隐藏，candidates 是唯一能看的"别人怎么做"，若先看它再倒推标准，会把"多数候选的做法"误当成"spec 的要求"（过拟合，见规则 02）。正确顺序：Prompt 立意草稿 → 看 candidates 归纳"区分好坏的维度" → 写 rubric → 编码。candidates 提供**证据**，Prompt 提供**要求**。

## 02. 多数不等于规格 (consensus-not-spec)

K 个候选都做了同一件事**不等于**这件事是 spec 要求的。可能他们都犯了同一个错。判分按 spec 走，不按"多数候选这么做"走。

## 03. 歧义外显 (explicit-ambiguity-log)

任何"可松可严"的解读，必须写成一条 `Amb-N` 条目，给出初始选择 + 1 句理由，不能悄悄按某种理解写死。

## 04. 全通过自我怀疑 (all-pass-suspicion)

如果心算发现 K 个候选全部 PASS，停一下问自己：是不是有歧义决策选错了宽松版本？至少把每条 `Amb-N` 的严格版重新过一遍。

## 05. 谓词必须可证伪 (falsifiable-predicate)

写完一条原子谓词 Pi 后立刻问自己：想象一个候选把这件事**做错**或**没做**——检查能不能抓住？想不出反例 → 这条太抽象，必须细化或拆分。反例必须针对**交付物内容**而非**文件壳/子串壳**——"文件存在但内容空/错"也算反例；仅路径存在或单一锚点命中不能作为唯一满分路径（与规则 09 叠加）。每条 signal 写完，在文档注释里留一句反例标注。

## 06. must-have 全部进闸 (must-have-gate-is-absolute)

标了必检项的 signal **全部**进闸，不许挑子集。如果某条不该卡整体，就把它降级为加分项，并在 `verifier_summary.md` 写理由。

## 07. 三档打分需要具体例子 (three-tier-docstring)

写每条 signal 实现时，在文档注释里显式列出 0 / 0.5 / 1.0 三档各自对应什么具体情况，不能只写"部分符合给 0.5"这种空泛描述。

## 08. signal 命名要语义化 (semantic-signal-naming)

不需要对齐任何隐藏的官方字段名，但自己的 `signals`/`breakdown` key 必须语义化（描述"在检查什么"，如 `report_file_valid`），且与 `rubric.md` 里列的 criteria 一一对应，方便下游做对齐。

## 09. 禁止纯关键词过闸 (no-keyword-only-pass)

每条 signal 内部多分支判定时：至少 1 条非兜底分支必须是结构性检查（读 JSON/YAML 字段、解析 markdown 段落、读 trajectory 工具名）；关键词/纯存在性/单一子串正则命中时得分上限 0.5，不能独立越过必检项闸门；在文档注释里标出哪部分是结构性检查、哪部分是关键词命中。

## 10. 覆盖率打分必须配 anchor (coverage-needs-anchor)

"命中 k/N 项即 PASS"型 signal，不能单独进必检项闸门，要配一条同名同等级的 anchor 信号；覆盖率 ≥0.99 的判定，须同时满足"命中里至少一半带 anchor"。

## 11. 谓词间不变量 (cross-predicate-invariants)

显式列出谓词之间的互斥/共生/连带关系，在 `grade()` 末尾用一个一致性检查函数逐条核对，违反就把涉及的必检项压到 0。

## 12. 满分门槛与别名上限 (full-match-alias-cap)

覆盖类必检项的满分门槛硬定为 100% 命中（样本量很小时才放宽，且必须写理由）；别名/同义词 OR 集合最多 2 条，多了就该改成结构性检查。

## 13. 硬闸命名与短路返回 (hard-gate-early-return)

命名带"不许/禁止/安全/硬性"含义的必检项一律视为硬闸：违规分支命中即直接返回 0 分，不许写成"违规且没有补救才算违规"这种 OR 救回逻辑。

## 14. 运行时契约 (runtime-contract)

grader 只许读：任务输入清单里列出的文件、agent 落盘的产物、传入的 `transcript` 参数。运行时拿到的是 `(transcript, workspace_path)`，**严禁**引用只在准备阶段才存在的目录名。每条 signal 在文档注释里标明数据来源（产物 / workspace 输入文件 / 原始轨迹）；`verifier_summary.md` 加一节列出每条数据来源路径，并做一次"每个来源至少能确认存在一次"的自检。

## 15. 可结构校验的必检项禁止均值闸门 (deterministic-gate-no-lenient-mean)

编码闸门公式前，对每条必检项问：能否用文件存在/字段值/数值区间/trajectory 工具名做结构性判定？只要有 ≥1 条答"能"，闸门必须是"全部必检项都 ≥0.99 且加分项均值达标"，不许用"必检项均值 ≥ 某阈值"这种宽松公式稀释。只有当**全部**必检项都是无结构锚点的主观维度时，才允许走 SKILL.md 描述的"纯 agentic_judge 闸门"（见规则 20/23）。`verifier_summary.md` 的 `## Gate Policy` 节必须写明具体用的是哪种闸门及判定依据。

## 16. 分数拉开度自检 (score-spread-selfcheck)

自我反思实跑后，计算 PASS 候选与 FAIL 候选的分数极差：极差 < 0.15 → 谓词过浅、判别力不足，不得宣称收敛，回去加锚点/加 fixture 对照/收紧闸门；极差 ≥ 0.25 且分布非全 PASS → 通过本项。

## 17. Fixture 真值优先 (fixture-truth-first)

这是防止"浅检过宽"最重要的一条规则，适用于所有需要结构性核对的必检项：

1. 满分路径必须**先**从 workspace **输入文件**读出可核对的真值，**再**与候选**产物**做字段级或数值级对照——不能颠倒顺序，也不能在 grader 内部自己编一份对照表（既不是从 workspace 输入读的，也不是候选产物）。
2. 仅靠关键词出现次数、章节标题命中、覆盖比例达标、宽阈值数值比较（如"相似度≥0.85 就算过"）这类路径 → 该 signal 上限 0.5，**不得**单独支撑必检项通过。
3. 禁止"命中 A 或 B 中任意一个就给满分"的 OR 救回写法；满分必须由多个独立条件同时满足（AND）达成。
4. 若必检项要求对候选做真实执行验证（见规则 19），期望结果同样必须从 workspace 输入派生，不能是 grader 里硬编码的样本集或临时目录里现造的假场景。
5. 在文档注释里标明：这条满分路径依赖哪个 workspace 输入文件、对照的是产物里的哪个字段。

**正例**：

```python
def grade(transcript, workspace_path):
    expected = _derive_expected_from_workspace(workspace_path)   # 第一步：先从输入读真值
    signals = {}
    signals["classification_correct"] = _score_against_expected(
        _read_deliverable_text(workspace_path), expected,        # 第二步：与产物逐项核对
    )
    ...

def _score_against_expected(deliverable_text, expected):
    """
    1.0 - 每条期望记录在产物里都能找到正确对应
    0.5 - 至少一半记录正确（不得单独进必检项闸门）
    0.0 - 少于一半
    """
    hits = sum(1 for rec in expected["records"] if _record_matches(deliverable_text, rec))
    ratio = hits / max(1, len(expected["records"]))
    if ratio >= 1.0:
        return 1.0
    if ratio >= 0.5:
        return 0.5
    return 0.0
```

**反例**：

```python
def _check_something(deliverable_text, hardcoded_keywords):
    # 问题：hardcoded_keywords 不是从 workspace 输入读的，是 grader 里现编的
    # 问题：子串命中代替字段精确核对
    return 1.0 if any(kw in deliverable_text for kw in hardcoded_keywords) else 0.0
```

**自检动作**：对一个 PASS 候选做"内容破坏"测试——把核心字段改错后重跑，该 signal 必须掉到 0.99 以下；否则说明这条信号没有真的在检查内容，是摆设，必须重写。

## 18. 过程类信号不得进必检项 (process-predicates-nice-only)

"是否在轨迹里咨询/阅读过某输入文件""工具调用序列是否完整"这类**过程**类信号，只能进加分项，不能因为"轨迹没展示某个动作"就单独判 FAIL。如果 Prompt 明确要求某输入必须被引用，改成检查**产物内容**是否体现了该输入的关键信息（规则 17），不能用"轨迹里出现过某次调用"代替。

## 19. 可执行交付物需要真实执行验证 (executable-needs-real-run)

当 Prompt 要求产出可运行脚本/命令/工作流时：必检项中至少 1 条必须是**执行型**信号——真的在候选的 `workspace_path` 上运行产物、探测其行为（退出码、输出、副作用），不能只靠"文件存在"或"命令文本里出现了某个子串"。执行验证**必须**在传入的真实 `workspace_path` 上进行，**禁止**在 grader 内部自建临时目录、构造一套假场景后在那套假场景上运行（候选命令在假场景上跑通不等于在真实候选 workspace 上正确）。期望结果同样要从 workspace 输入派生（规则 17）。命中"Code"相关 domain 时，参照对应 domain guide 的具体代码示例。

## 20. 主观维度必须走 agentic_judge (subjective-needs-agentic_judge)

看不到隐藏的官方评分细则，但很多任务的"对错"恰恰在主观叙述维度（论证是否成立、说明是否完整、语气是否得体）。这类维度**不允许**再用"找几个关键词/短语翻译成正则"的方式近似——必须调用 `judge_harness.invoke_agentic_judge()`，让 agent 真正读证据、给出带引用的裁决。哪些谓词属于"确实无法结构化核对"，参照 SKILL.md 的谓词分诊步骤逐条判断，默认拒绝进入这个分支，只有确认真的没有结构性锚点才允许。

## 21. 禁止用关键词冒充 agentic_judge (no-keyword-proxy-for-judge)

任何被分诊标为"走 agentic_judge"的谓词，其实现**必须**是 `invoke_agentic_judge(...)` 调用，禁止用关键词列表或正则表达式近似实现——这种写法比诚实的结构化检查更糟，因为它精度低却装作是"判断过了"。自我反思时必须 grep 自己 `grader.py` 里所有走 agentic_judge 的谓词对应的函数体，若出现关键词判断而不是 `invoke_agentic_judge` 调用，必须重写。

## 22. 裁判问题必须接地于具体谓词 (judge-prompt-grounded)

`judge_prompt` 与 schema 里的每个维度，都必须能一一对应到分诊阶段某条"走 agentic_judge"的具体谓词描述。禁止在编码阶段临时新增"整体质量怎么样"这种无锚维度——每个维度必须是具体、可举反例的判断。

## 23. 裁判结果默认只进分数 (judge-default-score-only)

`invoke_agentic_judge` 的结果默认只贡献加分项/连续分。只有当整个任务确认**完全没有**可结构校验的必检项时，才可以用 SKILL.md 描述的"纯 agentic_judge 闸门"（k≥5 采样、一致度≥0.8、不可用时判 FAIL）把它接入最终的 PASS/FAIL 判定。任何"部分可结构校验、部分主观"的混合任务，PASS/FAIL 永远只看可结构校验的部分。

## 24. 裁判库只拷贝不改写 (judge-harness-copy-only)

`judge_harness.py`（若某任务用到）必须是技能自带模板文件的逐字节拷贝。自我反思时用 `diff` 确认一致；发现想"改进"沙箱/投票逻辑——不要改，那是维护职责，改坏了会引入沙箱逃逸风险。

## 25. 裁判不可用时保守判定 (judge-fail-safe-on-unavailable)

`invoke_agentic_judge` 返回不可用（agent CLI 不存在/超时/k 次采样分歧过大）时：若该维度只影响分数，记 0 分，并把 `invoke_agentic_judge` 的原始返回值整个放进 `grade()` 返回值的 `judge_meta` 字段（结构化字段，不是拼进 `notes` 自由文本——后者容易被下游工具漏解析），不得静默当满分或直接忽略；若该维度是"纯 agentic_judge 闸门"，最终判定必须是 FAIL，不是 PASS。

## 26. 裁判维度需要 mutation 自检 (judge-mutation-selfcheck)

挑一个 PASS 候选，人为明显降低其相关维度的质量（删掉关键论证段落、替换成空洞套话），重跑判分，对应 agentic_judge 维度的分数必须明显下降；不降 → 说明 `judge_prompt` 没有真正接地到具体证据要求，回规则 22 重写。

## 27. 裁判分诊需要回流自检 (judge-routing-leak-selfcheck)

逐条检查所有走 agentic_judge 的谓词，重新问一遍"这条真的不能结构化核对吗？"——特别警惕谓词描述里出现具体字段名/数值/文件名（这些通常可以做结构化检查）、或命中的 domain guide 明明是 `mostly-deterministic` 却仍标了多条走 agentic_judge。发现偷懒路由，搬回结构化检查重写。
