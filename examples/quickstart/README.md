# quickstart：6-task open-ended 端到端 demo

这不是一份"应该能跑通"的脚手架说明——这个目录里的 `produced/` 和 `report/` 是**真的用一个 agent 跑过一遍 verifier-author 流程后留下的产物**，不是手写的示例。目的是让你不需要拿到完整 150-task 原始数据集，就能看到（并亲自重跑）"给一个开放式任务写一份 verifier"这件事具体是怎么发生的。

## 目录结构

```
examples/quickstart/
├── skill/              交付物 skill 的一份快照（见下「这份 skill 是哪个版本」）
├── bench/              6 个 task 的"考题+答案"两层结构（stage 产物，见 benchmark/README.md）
│   └── tasks/<task_id>/
│       ├── verifier_author_inputs/   考题：task_md + inputs + 8 个模型的候选答卷
│       └── gold_verifier/            答案：官方 grader/labels（只在阅卷时用，author 从未见过）
├── produced/<task_id>/ author 真实生成的 grader.py / rubric.md / verifier_summary.md
│                        （部分 task 还带一份 judge_harness.py，见下）
├── report/              evaluate_bench 跑出来的一致性报告
└── scripts/
    ├── stage_demo.py    重新从原始数据 staging 这 6 个 task（需要你本机有 origin_data/）
    ├── run_author.sh    对单个 task 用你自己的 agent CLI 重新跑 author
    └── run_evaluate.sh  跑阅卷，重新产出 report/
```

## 这 6 个 task 是怎么选的

同一命名风格（`task_<slug>`），上游都来自 PawBench 的同一个子来源 **pinchbench**（见 `origin_data/SOURCES.md`），且都是**开放式（open-ended）**任务——没有单一"标准答案"，需要 verifier 自己归纳主观评分维度，而不是核对几个确定性检查点：


| task_id                            | 任务类型                     | 判分挑战                |
| ---------------------------------- | ------------------------ | ------------------- |
| `task_blog`                        | 写一篇 500 字博客              | 内容质量/主题贴合度，没有唯一正确文本 |
| `task_contract_analysis`           | 读 PDF 合同做法律分析            | 风险识别是否到位，见仁见智       |
| `task_meeting_advisory_attendees`  | 从会议逐字稿提取与会人信息            | 角色/发言性质判断需要理解上下文    |
| `task_meeting_gov_data_sources`    | 从 NASA UAP 听证会逐字稿提取数据来源  | 相关性与局限性描述的完整度       |
| `task_video_transcript_extraction` | 拉取 YouTube 字幕并写摘要        | 摘要质量、要点取舍           |
| `task_gh_issue_triage`             | 给 GitHub issue/PR 做优先级分诊 | 优先级排序本身就是判断题        |


挑选标准：在 `260701_agenticjudge` 实验 iter_0→iter_3 的四次独立重跑（同一份 v0 skill，重复采样）里，这 6 个 task 的 agree/8（与官方判分一致的候选数）**持续偏高、波动小**——即便这份 skill 从未被真正迭代过，它在这批 open-ended task 上的表现本身仍然是真实、可复现的信号，不是一次性的好运。

## 已经跑出来的结果（本仓库当前 checkout 上重新跑的，非直接抄实验旧报告）

评测方法与真实实验完全一致（见 `benchmark/README.md` §5）：author 全程在隔离沙箱里只能看到 `skill/` 与该 task 的 `verifier_author_inputs/`，物理上不存在 `gold_verifier/`；阅卷阶段才把 author 产出的 `grader.py` 拿去跟 8 个候选答卷的官方判分比对。

```
覆盖率：可比 48/48 obs（6/6 task 全覆盖）
D1 outcome micro=0.854  macro=0.854
D1′ 误判：false_pass=7  false_fail=0     ← 与本仓库全部实验一致的模式：判得太宽，不是太严
D2 score：MAE=0.350  Spearman=0.503      ← 明显弱于 D1，原因见下方「一个真实的负面发现」
D3 排序：pairwise=0.346  Kendall=0.308（107 对）
```

完整报告：`[report/eval_report.md](report/eval_report.md)`、逐观测明细：`[report/eval_per_obs.jsonl](report/eval_per_obs.jsonl)`。

按 task 分解（agree = 与官方判定一致的候选数 / 8）：


| task_id                            | agree | false_pass | false_fail |
| ---------------------------------- | ----- | ---------- | ---------- |
| `task_blog`                        | 8/8   | 0          | 0          |
| `task_meeting_gov_data_sources`    | 8/8   | 0          | 0          |
| `task_gh_issue_triage`             | 8/8   | 0          | 0          |
| `task_contract_analysis`           | 6/8   | 2          | 0          |
| `task_video_transcript_extraction` | 6/8   | 2          | 0          |
| `task_meeting_advisory_attendees`  | 5/8   | 3          | 0          |


## 一个真实的负面发现：agentic_judge 在这次 demo 里根本没打到

这份 skill 的核心卖点是"结构上没法确定性核对的谓词，真的调一次 LLM agent 判分"（`judge_harness.py` 里的 `invoke_agentic_judge`）。**但在生成这份报告的运行环境里，48 个观测对应的全部 68 次 `invoke_agentic_judge` 调用，`judge_meta.available` 全部是 `False`**（`report/_judge_trajectories/` 下落盘的轨迹文件全部是 0 字节，子进程在 1-2 秒内就失败退出，没有产出任何可解析结果——大概率是这个非交互 shell 环境里 `cursor-agent` 缺少可用的登录态/会话上下文，不是 harness 本身的 bug）。

这件事本身没有被"修复"或掩盖，因为它暴露了两个值得记录的真实情况：

1. `**invoke_agentic_judge` 的失败契约本身是对的**：调用失败时归一化成 `available=False`、grader 不崩溃、`outcome_passed`（只看确定性 must-have）完全不受影响——这解释了为什么 D1（0.854）依然体不错。
2. **但 D2（score 级 MAE/Spearman）被系统性拖低**：翻看 `grader.py`（例如 `examples/quickstart/produced/task_blog/grader.py`），`judge` 不可用时它把每个 `agentic_judge_`* 维度**填 0 分**再纳入 score 均值，而不是把该维度整体排除出均值——等价于把"没打到裁判"错记成"裁判打了 0 分"，把本该只反映确定性信号的 score 硬拖低了一截。这是 author agent 自己写出来的降级逻辑里一个真实的设计缺口，不是我们事后发现改代码改出来的问题，保留 `grader.py` 原样是为了如实展示这一点。

想自己复核：`grep -c '"available": true' report/_judge_trajectories/**/*.jsonl` 或直接检查文件大小（全 0 字节）；也可以在你自己已登录好 `cursor-agent`/`claude`/`codex` 的环境里重跑 `run_evaluate.sh`，看这个数字是否变化。

## 怎么复现

**只看已有产物**（不需要任何 agent CLI/API key）：

```bash
cat examples/quickstart/report/eval_report.md
```

**重新跑某个 task 的 author 步骤**（需要你自己登录好的 `cursor-agent` / `claude` / `codex`）：

```bash
cd examples/quickstart
./scripts/run_author.sh task_blog composer-2.5 cursor-agent
./scripts/run_evaluate.sh
```

**从零重新 staging 这 6 个 task**（需要你本机有完整 `origin_data/`，见根目录 README「数据与许可」）：

```bash
python examples/quickstart/scripts/stage_demo.py
```

## 局限说明（不藏着）

- 这 6 个 task 的 `gold_verifier/`（官方评分标准/参考答案）也一并公开在 `bench/tasks/<task_id>/gold_verifier/` 里，方便你自己核对上表数字——但这意味着**这 6 个 task 不能再用来测试新版 verifier-author skill**（它已经"见过答案"了，任何人拿这 6 个 task 复测都不是干净的评测）。真正的能力评估要用完整 150-task benchmark 的 train/test split（数据不随本仓库分发，见根目录 README）。
- 这 6 个 task 是**从"表现好、稳定"的角度主动挑出来的**，不是随机抽样，也不是完整 benchmark 上的代表性切片——本 README 的数字只能说明"这份 skill 在这类 open-ended 任务上能做到什么程度的上限"，不能拿来推断它在其余 144 个 task 上的整体能力（那部分的诚实汇报见各实验目录的 `reports/final_report.md`）。
- author 的物理隔离（沙箱里根本不存在 `gold_verifier/`）是这次 demo 的反泄漏保证；本仓库正式实验额外做的"轨迹取证"（`benchmark/tools/leak_scan.py` 扫 agent 工具调用轨迹）在这次 demo 里没有对应的可用轨迹格式，属于简化，不影响本次隔离的有效性，但如果你要写论文/报告引用这份 demo，请说明这一点。
- 6/8 的样本量对任何一个 task 都撑不起统计显著性，本 README 的"按 task 分解"只是定性展示，不是严谨的能力评估。
- agentic_judge 在本次运行里没有真正打到（见上一节）——这份报告实际展示的是"确定性 + 结构化 nice-to-have 信号"的判分能力，agentic_judge 这个设计方向本身还没有被这份 demo 真正验证过。

