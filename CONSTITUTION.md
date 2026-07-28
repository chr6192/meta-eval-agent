# Meta-Eval-Agent 仓库宪法

> 这是本仓库做开发时的最高原则。任何 PR、迭代、子代理工作都要先读它一遍。
> 与下层文档冲突时，以本文件为准。

---

## C1. 资产形式：Anthropic Skills 协议（中文）

**规则**：meta-eval-agent 的可重用部分一律落成 Skills，不写成 `prompt + 脚本` 的"一次性集合"。

- 每个 skill 至少含 `SKILL.md`（带 YAML frontmatter：`name` + `description`，可选 `allowed-tools`）；脚本作为附件存在但**接口由 SKILL.md 描述**。
- 所有 skill 内容用**中文**，包括 frontmatter 的 description 字段。
- 一个 skill 只做一件事。多 skill 组合替代"巨长的单体 prompt"。
- 评判一个改动是否 skill 化是否到位：能不能让另一个 host 直接 plug 进来用？能 → 合格；不能 → 还在"脚本风"。

---

## C2. 训练/测试集物理隔离（不许 hack 测试集）

**规则**：测试集的标签和 trajectory 在**整个迭代过程**中不许进入 meta-eval-agent 的判断回路。

- `data_split/test.json` 是黑盒；只有最终一次评估能打开。
- 任何 `eval()` / `analyze()` / `inspect()` 类操作如果触及测试集，必须在代码里加显眼断言 + 注释说明授权。
- 训练集用来选超参 / 改 skill 内容 / 修 prompt。测试集用来汇报，不用来调。
- 如果某个改动只让训练集涨分但测试集掉，承认它是过拟合，回退。

---

## C3. Ground Truth 物理隔离（不许 verifier 偷看答案）

**规则**：verifier_author 看到的上下文里**不能**出现 `gt/`、`optimal_*`、`expected_*`、`reference_*`、`solution_*`、`answer_*`、`golden_*`、`ground_truth*` 等命名的文件或目录。

- 隔离在**数据层**做，不只是 prompt 层提一句"请不要看"。
- 隔离失败 = 实验作废。任何新 evaluator 第一项断言：扫描 ctx 目录，发现 GT 嫌疑文件就 abort。
- 但运行时（eval 阶段）produced grader 自身可以选择是否读取这些文件——这是 grader 设计自由度，不在隔离约束范围内。

---

## C4. 实验科学性：可重现、有对照、有泛化检查

**规则**：每次迭代都要交代清楚"改了什么"、"在哪测的"、"对照是什么"、"是否 overfit"。

- 每轮迭代必须有 `iter_NN_report.md`，至少包含：动机、改动点、训练集指标 delta、是否在测试集复测、过拟合判断。
- 不许 cherry-pick 子集报喜。展示训练集准确率时给出**全 train set** 或**均匀随机抽样子集**的数字。
- 任何 "1 个任务的 fix" 必须说清"是否会让别的任务掉分"，不许把单点修复包装成普遍提升。

---

## C5. 报告可读性：通俗易懂，少抽象名词

**规则**：报告用大白话写，不堆砌"涌现 / 范式 / 锚定 / 解构 / 自洽"等空词。

- 一句话能说清的，不写五句。
- 关键数字（准确率、任务数、错误次数）必须有具体值，不写"显著提升"。
- 每个结论后面跟 1-2 个具体例子，否则不算结论。
- 写完自问：能给数据科学家或产品经理直接看吗？能 → 合格。需要"解释一下专业术语"→ 重写。

---

## C6. 失败的处理：先存证、再分析、最后改

**规则**：当一轮迭代没拿到预期效果，禁止"先随便改改试试看"。

- 第一步：把失败 case 落进 `analysis/iter_NN_failures.md`，列具体任务 id 和触发链路。
- 第二步：聚类失败模式（≥3 个 case 才算"模式"，单点是噪声）。
- 第三步：基于模式提改动假设，写进 `process.md` 当前轮的"假设"段。
- 第四步：实施改动，跑一次小批次（≤16 task），看假设是否成立。
- 第五步：成立才推到大批次。不成立 → 假设作废，回 C6 重来。

---

## C7. 计算预算：每轮要轻、可中断、可继续

**规则**：单次 claude -p 调用约 5-20 分钟，80 任务 × 3 framework × N 轮 不是无限的。

- 每轮迭代默认在 **8-16 个 task 子集**上做实证验证；满训练集评估每 5 轮做一次。
- **全量豁免**：实验可在自己的 `plan.md` + `process.md` 里显式声明「每轮跑全 train 集」（理由：轮间在同一 task 全集上比较才是真比较，子集会引入抽样噪声、掩盖此消彼长）。声明后豁免上一条的子集默认，但必须在 `process.md` 记录该选择、受影响轮次与算力预算量级。
- 任何长时间运行必须用 jsonl 增量写盘，能从中断点继续。
- 已经跑过的 (task, version) 组合默认从 cache 读，不重跑。
- 报告里要诚实写"哪轮跑了多少 task"，不要拿"代表性子集 N=12"假装是"完整 N=80"。

---

## C8. 信息泄漏防御：物理隔离 + 轨迹取证

**规则**：verifier_author 写 grader 时，绝不读取 gold（答案）路径下的内容。

- 第一层 · **staging 物理隔离**：gold 全部落在 `gold_verifier/`，不进考题层 `verifier_author_inputs/`；`self_test` 用 `lib.is_gt_path` 自检考题层无 GT 残留（C3/C17）。
- 第二层 · **轨迹取证**：扫 author agent 的执行轨迹（`leak_scan.scan_trajectory`），看它实际发起的工具调用是否触达 `gold_verifier/`——读了就是泄漏，没读就是干净，只看真实动作、不做源码启发式猜测。

> 历史教训：旧版「AST/grep 静态扫 grader.py 源码子串」（`answer_`/`reference_` 等）误报率极高——它分不清「候选自己的答卷」与「标准答案」，已废弃。判泄漏的唯一可信信号是「agent 是否真的读了 gold」。

---

## C9. 子代理使用：专业的事交给专业的代理

**规则**：本仓库的 host 是协调者，重活包出去给 subagent。

- 长文档分析 / 多文件 grep / 失败聚类等"消耗大量上下文"的工作 → spawn Explore 或 general-purpose subagent。
- 写设计 / 改进假设 → spawn Plan subagent。
- 跑真实 LLM 调用 → 走 `claude -p`，host 不亲自做判分推理。
- subagent 返回结果后 host 必须复核关键数字（不要无脑相信总结）。

---

## C10. 命名一致 / 文档同步 / 不留断头链接

- 文档里引用某个文件路径，该路径必须存在。
- 改 schema 字段时，先改单点真相源（如 `CONSTITUTION.md` 或 `skills/.../SKILL.md`），再批量同步下游。
- 不写"TODO 之后会补"，要么写要么删。

---

## C11. Orchestrator-loop：监督信号只能来自 audit，不能来自 oracle 偷看

**规则**：当主体（orchestrator）在多轮生成-测试-审计闭环里调 SKILL 时，**唯一**允许喂给下一轮 skill-optimizer 的输入是上一轮的 audit 报告（聚类失败 + 假设根因）。

- audit 报告**不能**包含 test 集任意 task 的 id、failure 列表、derived/official 对比。
- audit 报告**不能**包含官方 grader 的代码或 per-criterion breakdown。
- audit 报告允许包含：train 任务名、derived vs official 的 PASS/FAIL 二值、自然语言聚类后的失败模式。
- 违反 = 实验作废，回退到上一个干净的 SKILL 版本重新跑。

---

## C12. 角色物理分离：optimizer / author / auditor 三个 subagent 不共享上下文

**规则**：在 orchestrated 闭环中，三个 subagent 的 context 严格隔离。

- skill-optimizer 只看：当前 SKILL + 上轮 audit 报告。**不看** trajectory、不看 candidates、不看 grader.py。
- verifier-author 只看：单 task 的 ctx（task_md + verifier_hints + inputs + candidates，已经 GT 隔离过）+ 当前 SKILL。**不看** audit 报告、不看 official PASS/FAIL。
- verifier-auditor 只看：评测器输出（derived vs official 二值）+ produced grader.py + train 任务的 ctx。**不看** SKILL 内部细节、不写 SKILL diff。
- 任何"我代两个角色干活"的简化 = 实验作废。

---

## C13. SKILL 版本化与回滚

**规则**：每轮迭代结束保存 SKILL 快照，不许原地覆盖。

- 路径：`skills/verifier-author/SKILL.md` = 当前生效版本；`skills/verifier-author/_versions/v7.{N}.md` = 历史。
- 每轮 optimizer 产物落到 `_versions/`，再 promote 成 `SKILL.md`。
- 任意一轮 audit 报告显示**新版相对老版回退**（train strict 准确率绝对值降 **3pp** 以上），自动回滚到上一版，并在 `process.md` 标注"v{N} aborted"。
  - **[2026-06-25 收紧]** 原为 5pp；260622 实验 iter_4 回撤 3.7pp 未触发 5pp 线，坏改动（AND 过严）残留 v5–v8，false_fail 从 66 升至 96，是此次收紧的依据。

---

## C14. "一轮 verifier_author 迭代" 的硬定义

**规则**：以下三件事都做完才算一轮，少一样都不算。

1. **改 SKILL**：在 `skills/verifier-author/_versions/v{N}.md` 落新版（C13 强制）
2. **用新 SKILL 跑 LLM**：调 `claude -p` 让 verifier_author 在 ≥ 8 个 train task 上**重新生成** grader.py（不是改旧的）
3. **跑评测 + 对比上轮**：跑 evaluator，把 v{N} 的 Strict/Auto-only/Rank 几个数字与 v{N-1} 同 task 子集对比，写进 `reports/iter_NN.md`

**不算一轮的**（不许编号、不许进 iter_index 当一行）：

- 改 evaluator / leak_scan / 工具脚本 — 标 `tooling-NN.md`
- 写分析 / 诊断 / 失败聚类报告 — 标 `analysis-NN.md`
- 改 SKILL 但没跑 LLM 验证 — 标 `draft-vN.md`（在 `_versions/` 里待用，不进 iter 计数）
- 在已生成 grader 上做后处理（regex / AST 改写源码）— 见 C15

**违反后果**：把"假轮次"从 iter_index 删除；`process.md` 加标注"iter_NN withdrawn (no LLM verification)"。

---

## C15. 后处理篡改 ≠ 迭代 verifier_author

**规则**：用 regex / AST 改写已生成 grader 的源码，**只**能当 "天花板估计实验"，不能当作 verifier_author 迭代的结果。

- 这类实验的产物路径必须放 `runs/ceiling_probes/`，**不**放 `runs/iters/`
- 报告里展示数字时必须显式标注 "**ceiling probe（非 LLM-loop）**"，禁止与真迭代数字混表
- 不许说"经过 NN 轮迭代准确率从 X% 提到 Y%"，如果 X→Y 是后处理改写得到的
- 后处理可以**辅助** verifier_author 迭代（用来定位 systematic 失败模式），但**不替代**它

**教训来源**：iter_v6 实验里把"iter_01-08 机械修复 phase2 已生成 grader"标成 8 轮 verifier_author 迭代，是虚假报数。这 8 轮没有任何 LLM 调用，只是脚本改源码。

---

## C16. LLM 调用账本必须公开

**规则**：每个最终报告必须含一张 "LLM 调用账本" 表，作为该实验"做了多少真迭代"的唯一可信凭据。

字段包括：

| iter | claude -p 调用次数 | task id 列表 | 总耗时（秒）| 用的 SKILL 版本 |
| :-: | :-: | --- | :-: | --- |

- 每行对应一次 verifier_author 真调用（按 C14 定义）
- 表的行数 = "真迭代轮数"，**不许**用其它分母（"广义轮"、"包含设计层的轮"等）冒充
- 报告标题里如果出现 "N 轮迭代"，N 必须 = 此表行数
- 当算力不允许跑足够多轮时，**老实写**"做了 K 轮 LLM 真迭代 + M 个 ceiling probe + L 个 draft skill version"，三组数字分列，不要相加报为一个 N

**教训来源**：iter_v6 实验报告里写"26 轮迭代"，实际只有 1 次 LLM 调用批次（iter_11 的 8 个 task），其余 25 项是机械修复 / 工具改进 / 文档分析 / 草稿 SKILL。两个数字差了 26 倍。

---

## C17. 评分侧知识对 verifier-author 不可见（隔离再扩一层）

**规则**：凡是 **agent 跑 task 时看不到、只在判分时才用**的"评分侧"内容，一律对 verifier-author 物理隔离，进 `gold_verifier/` 层，不进 `verifier_author_inputs/` 层。

- 隔离对象：`## Grading Criteria`、`## LLM Judge Rubric`、`## Automated Checks`（官方 grader 源码）、`## Expected Behavior`、frontmatter 的 `grading_type / grading_weights`。
- verifier-author 只能拿到 **agent 视角的输入**（`## Prompt` + 环境 frontmatter）+ **candidates**（多 harness×model 探索环境的产物）。
- verifier-author 必须**自主归纳**评分标准（criteria / rubric，落 `rubric.md`），再据此写 grader。
- 这是 C3（GT 文件隔离）的扩展：GT 是"答案"，评分标准是"答案的另一半"。两者都不许进 verifier-author 的输入层。

**理由**：喂评分标准 = 把判分逻辑直接给它，测不出"能不能像人工标注员一样，自己从产物里想清楚怎么算做对了"。

---

## C18. gold = 数据自带 built-in verifier 的判定

**规则**：benchmark 的 gold（标准答案）是数据**自带 built-in verifier** 的判定，generated verifier 的目标是向 gold 对齐。

- 主字段 `passed` 取自 framework 跑分 `results[].passed`（含 LLM judge 维度）。
- 自带 verifier 视为**置信**（来自成熟 benchmark），不质疑、不重定义。
- **不许**用 generated verifier 自己的产出反过来定义或污染 gold。

---

## C19. 评价用多维一致性，不止二值

**规则**：评价 generated verifier 好坏，必须报**多维一致性**，不许只用单一 `passed/failed` 一致率下结论。

- 至少含：D1 outcome 一致（micro + macro）、D1′ false-pass / false-fail 分解、D2 score 对齐（MAE + 相关）、D3 排序一致（判别力）。
- **false-pass**（把坏 candidate 判过，漏判）与 **false-fail**（把好 candidate 判挂，误判）**必须分开统计**——两者代价不同，混在一个一致率里会掩盖问题。
- 维度定义见设计文档 §6。

---

## C20. 可达性诚实：区分"verifier 差"与"任务够不着"

**规则**：有些评分维度 generated verifier **物理够不着**——依赖 LLM judge（审美/语义）或依赖 oracle（gt 参考解对比）。报指标时必须把这部分和"verifier 能力缺陷"分开。

- 用 `reachability.json` 标注每个评分维度依赖：`workspace / transcript / llm-judgment / oracle`；`reachable = depends_on ∈ {workspace, transcript}`。
- 同时报"全维度对齐度"和"可达维度内对齐度"。**不许**把物理不可达的失分算作 verifier 写得差。
- reachability 用**静态解析官方 grader**生成（看每个 criterion 读什么文件/走什么权重），不靠拍脑袋。

**理由**：calendar task 的 `optimality_ratio` 读 `gt/optimal_unscheduled.json`，gt 被隔离后 generated grader 无论多好都复刻不了——这类失分不该算到 verifier 头上。

---

## C21. benchmark 是 self-contained 资产，且必须自检有效性

**规则**：benchmark 落成 **self-contained 物化快照**（可移植、可版本化），判分回路**不依赖原始数据的目录结构**；GT / 评分侧隔离在 stage 时一次做死。

- benchmark 是**底层数据资产**，train/test split 只是其上的**视图**，不绑定单次实验。
- benchmark **不假设"数据就是对的"**。stage 后必须跑有效性自检并落 `_stage/validity_report.md`：
  - **gold 自洽**：官方 grader 重跑 vs gold 一致性，列出不一致 task。
  - **区分度**：标全 pass / 全 fail 的无区分 task。
  - **可达权重分布**：标天花板被 oracle/llm-judge 压低的 task。
- 正确性自检（GT 隔离 / schema / gold 可跑 / 抽样）与有效性自检并列，二者皆过才算 benchmark 可用。

---

## C22. 交付物 skill 必须 bench-agnostic，可移植到无 gold 生产

**规则**：本实验的最终交付物是**单个 `verifier-author` skill**——一个在**没有 gold 可参照的 agent 数据合成**环境里，作为 agent 跑在 claude code / codex / cursor agent 中、靠自身 agent-loop 的 self-reflection 为 task+candidates 合成 verifier 的代理。benchmark（gold / labels / 官方评分标准 / train-test split / 编排器 / auditor / optimizer）只是**训练-测量脚手架**，不是产品的一部分。因此**交付物 skill 里绝不允许烤进任何"只有 bench 才成立"的假设**——一旦烤进去，到了生产环境就是哑火或误导。

- **区分两类 skill，不许混**：
  - **交付物（部署到生产，必须 bench-agnostic）**：仅 `verifier-author`。
  - **bench 迭代机器（仅训练期，永不部署）**：`experiment-orchestrator`、`verifier-auditor`、`skill-optimizer`——它们的本职就是吃 gold/audit/evaluate 驱动迭代，引用 gold/官方判定是对的，但**不得**把这套依赖混进交付物 skill。
- **编排器不替 bench 判质量**：`experiment-orchestrator` 不内置任何"验收 gate + 重试"来判 verifier 好坏——verifier 质量**只**由 benchmark 的 `evaluate_bench` 多维结果给出（C19）。无 bench 根据的启发式 gate（如 mutation kill_rate 阈值）是假信号，禁止用作编排器的质量裁决（C24）。质量改进走「audit→optimizer→下一轮全量重生成」闭环，不走单轮内置重试。
- **交付物里禁止的 bench 框架措辞**：「评分标准对你隐藏 / 已物理隔离 / 官方 rubric / 官方 `automated.X` / 官方 LLM Judge / 与官方 ground truth 对齐」等——这些都预设「存在一份官方标准、只是你看不到」。正确框架是「**没有现成评分标准，从任务意图自主构建**」（操作行为完全相同，但不泄漏 bench 的测量设置）。
- **交付物的质量自检必须 gold-free**：任何依赖 gold/labels/官方判定的 gate（如"与 ground truth 一致率 ≥ X"）只能活在 bench 训练期，**不得**作为交付物 skill 的内建步骤。生产期的质量保障只能靠**无监督代理**：mutation/判别力自检（破坏产物后 grader 应翻 FAIL）、意图自构的严谨度、反泄漏护栏。诚实承认能力边界——无 gold 时失去"对真相的直接校验"，这是事实，不掩盖（C5）。
- **反泄漏护栏保留**：交付物里"不读答案目录、不硬编码答案/候选身份"是**防过拟合的通用好规则**，在无 gold 生产里无害且有益，保留。
- **不留决策无关的噪音**：交付物 skill 与面向读者的文档不保留"不进任何决策"的探索性维度或死内容（徒增 agent 与读者负担）；移除决策交给 git 历史承载，**不在工作树文档里留 removal-note**。

**理由**：在 bench 上把一致率刷高不是目的，**产出一个"到了没有答案的真实数据合成里、还能自己从任务意图写出好 grader"的 skill** 才是目的。衡量交付物是否合格的终极问题：把它原样丢进一个没有 gold、没有 auditor/optimizer 的环境，它还能不能独立、正确地工作？

**受影响**：①（2026-06-22）D4(criteria 对齐)维度移除、satisfiability gate 收缩、"隐藏官方标准"措辞 bench-agnostic 化。②（2026-06-23）顶层 `meta-eval-agent` 改名 `experiment-orchestrator` 并降为「实验期机器」，其内置验收 gate（files/mutation）+ 重试**全部移除**——verifier 质量改由 bench `evaluate_bench` 裁决；交付物收敛为单个 `verifier-author`（生产 agent + self-reflection loop）。

---

## C23. 实验记录不可变；机制变更靠重跑，不靠改历史

**规则**：已落盘的迭代记录是**不可变的事实账本**，记录"当时用什么方案、得到什么结果"。当 SKILL / 工具 / 度量机制发生重大变更，正确做法是**新开实验重跑**产生新结果，**绝不**回头编辑历史记录使其符合新方案。

- 不可变对象：`process.md` 的日期小节、`reports/iter_*` 报告、`_versions/` 快照、LLM 调用账本。
- 改历史 = 既 falsify 事实，又制造叙事自相矛盾（如删掉某规则却留着"为它新增 X"的记录）。
- 旧记录里基于已废弃机制的结论，**保留为历史**；要对照就用「污染版 run vs 干净版 run」并列，而非抹除旧的。
- 推论：变更影响了既有实验的**优化路径**（而不仅是数字）时，必须新开目录重跑，不能就地打补丁续上。

**教训来源**：2026-06-23 leak_scan 由"静态扫源码"重构为"轨迹取证"后，选择新开实验冷启重跑，而非在已落盘的旧实验记录上打补丁续跑；且旧式 author 日志是 text 格式、无工具调用事件，新机制在技术上也无法补算到旧轮次。

---

## C24. 判定基于事实行为，不基于易误报启发式；假信号比无信号更糟

**规则**：任何"检测 / 判定"（泄漏、作弊、合规、回滚触发…）优先建立在**可观测的事实动作**上（agent 实际做了什么、读了哪个文件），而非对产物文本 / 源码的启发式猜测。

- **假信号比无信号更糟**：一个高误报的指标会**污染优化路径**——optimizer 去追噪声、auditor 误判根因、一整轮迭代预算打水漂。宁可暂时没有这个信号，也不要一个会骗人的。
- **彻底重构，不打补丁**：发现度量有系统性误报，剥离重建（换到事实信号），不是叠加更多启发式去压误报；并主动审视它**是否已污染既有结论 / 优化路径**（污染则按 C23 重跑）。
- **可人肉审核、可解释**：关键判定机制必须能把命中逐条连同证据列出来给人复核（写一个 review dump 即可），机制本身能用大白话讲清（C5）。

**教训来源**：旧 leak_scan 静态扫 grader 源码子串（`answer_`/`reference_`/`expected_` 等），跨 3 轮 232 条命中里 ~99% 是误报（把"候选自己的答卷 answer / 任务的 cross_reference"误判成读答案），还把 iter_1 整整一轮的优化（新增 M22）误导去治这个噪声。改为 `scan_trajectory`：只看 author 轨迹的工具调用是否真的触达 `gold_verifier/`，读了即泄漏、没读即干净（见 C8）。

---

## C25. 实验目录文档分工：process.md 是唯一"面向历史"的文档，其余只面向当下

**规则**：单个实验目录下，"过去发生了什么/为什么这样改"这类历史叙事**只允许存在于 `process.md` 一处**；其余文档只描述"现在是什么样、现在怎么操作"，不得复述历史、不得提及任何已废弃/已改名的旧特性——哪怕加"已废弃"注解也不行。进度追踪也不许人工开二份。

- **`plan.md`** 只写**本次实验自身、面向未来的方案设计**（目标、原则、协议、退出条件、当前资产结构）。**禁止**出现"与上一个/历代实验的差异对比"、"起点如何从旧版继承而来"这类历史叙事；起点只给一句无历史细节的事实指针（如"起点 SKILL = `v0_baseline_agenticjudge`，继承来源见 `process.md`"）。
- **`README.md`** 只放**面向当下操作**的稳定参考——入口导航、一键跑法、环境变量、编排约定、手动调试步骤。**不放**任何历史叙事、差异说明或旧命名对照表——这类内容看似"稳定"，实质是"过去怎样、现在改成怎样"，属于历史范畴，一律归 `process.md`。
- **`process.md`** 是全实验目录里**唯一**被授权"面向历史说话"的文档：开工前"起点说明"一节写清楚相对**直接上一个实验**的差异（更早代际只给指针，不复制，见 C23）；旧特性命名/迁移对照表也放在这里；之后逐轮追加事实流水账。
- **不额外手写第二份 SOP/进度清单**：如果编排脚本（如 `run_experiment.sh`）本身就是可执行、可断点续跑的 SOP，且 `STATUS.md` 是脚本自动刷新的当前状态快照，就不要再手工维护一份 `todo.md`/checklist 去复述"做了什么、接下来做什么"——手工文档会跟脚本实际行为脱节，产生虚假进度记录。进度可见性只认 `STATUS.md` + `process.md`。
- 任何文档一旦出现已被移除/改名的特性名（旧规则前缀、旧文件名等），判定为 **C10 违规**：不是"加注解说明已废弃"就算合规，而是**整条移除**，只在 `process.md` 保留。

**教训来源**：
1. （2026-07-02 首次）`260701_agenticjudge` 的 `plan.md`/`README.md`/`process.md` 三处都各写了一份"EX1/EX2/EX3 如何被替换"的说明，且互相冲突（`README.md` 编排约定表仍写"EX1/EX2/EX3 保护"，下方章节却说明这三个名字已不存在）。
2. （2026-07-02 二次，首次修复仍不彻底）初版 C25 曾误判"旧命名对照表"属于 README 该放的"稳定参考"——但只要内容是"过去怎样、现在改成怎样"就是历史，不该留在 README；同时 `plan.md` §5/§9 仍各自重复一遍对 `260630_composer25` 的继承解释，且直接写出了已废弃的 `v0_baseline.md`/`M33–M45`/`EX1/EX2/EX3` 等名字；`todo.md` 又与 `process.md`/`README.md`/`run_experiment.sh` 重复维护一份"做了什么/接下来做什么"。修复：`todo.md` 删除（`run_experiment.sh` 本身即 SOP，`STATUS.md` 已是自动进度快照）；旧命名对照表整段移入 `process.md`；`plan.md`/`README.md` 里所有历史叙事与已废弃特性名全部清除，只留一句无历史细节的指针。

---

## 元规则

- 这份宪法可以增删条款，但每次修改要同步在 `process.md` 记录原因和受影响的迭代轮次。
- 宪法不写"软建议"。每条都是硬约束。软建议放各 skill 的 `## 心得` 或 `## 已知坑` 节。
- **失败教训触发新条款**：每次发现一类系统性虚假报告（如"假轮数"、"上限估计冒充真结果"），必须在宪法加新 C 条款，附"教训来源"指向具体实验目录。
- **简洁优雅，不过度设计**：代码、机制、文档、宪法本身都遵循此原则——能用一条事实信号解决的不堆四层启发式，能两条款说清的不拆成五条。先解决真问题，不为假想需求预留架构。
