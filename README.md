# meta-eval-agent

**一句话**：用一个 agent（`verifier-author`）替代人工标注员——在没有参考答案、没有评分标准的场景里，给定"一个任务 + 若干候选答卷"，自动写出一份能打 PASS/FAIL 的判分程序（`grader.py`）。本仓库是围绕这个 agent 的**方法论 + 自建 benchmark**的公开留档。

## 这是在解决什么问题

Agent 数据合成 / RL 训练里经常需要给"某个 agent 任务做得对不对"打分，但很多任务**没有现成的评分脚本**——传统做法是找人工标注员照着任务意图写 verifier，成本高、难扩展。`verifier-author` 是让 LLM agent 自己干这件事：只给它任务的 `## Prompt` 和几份候选答卷（workspace 产物 + 执行轨迹），**评分标准和参考答案对它物理不可见**，它要自己归纳"怎么算做对了"、编码成判分程序，并在自己的 agent-loop 里通过 self-reflection（过宽自检、判别力自检、fixture 真值对照……）收敛到一份靠谱的 verifier。

## 三层结构

```
CONSTITUTION.md              仓库宪法：25 条硬约束（数据隔离/反泄漏/实验诚实性/版本回滚……）
        │
        ▼
benchmark/                   自建 benchmark：拿"任务 + 候选答卷 + 官方判分"改造成一场考试，
                              考核 agent 写出的 grader 与官方判分的一致性（D1–D3 多维指标）
        │
        ▼
训练期脚手架（内部迭代用，不随代码公开分发）：
                              author/auditor/optimizer 三角色隔离的编排闭环，
                              用来迭代打磨 verifier-author 这个 skill
        │
        ▼
交付物：verifier-author skill（见 `examples/quickstart/skill/SKILL.md`）
                              —— bench-agnostic，可直接搬进 claude code / codex / cursor agent 生产使用
```

`benchmark/` 与训练期脚手架里的 `experiment-orchestrator`/`verifier-auditor`/`skill-optimizer` **只是训练期的测量脚手架**，从不进交付物；唯一交付物是 `verifier-author` 这一个 skill（见 `CONSTITUTION.md` C22）。

## 30 秒跑一个端到端例子

不需要拿到完整的原始数据集，`examples/quickstart/` 已经自带 6 个开放式（open-ended，没有单一标准答案）真实 task（博客写作/合同法律分析/会议纪要提取 x2/视频转写摘要/issue 分诊），并且已经用真实 LLM agent 跑过一遍 `author → evaluate` 全流程、留了产出和报告：

```bash
cd examples/quickstart
cat report/eval_report.md          # 看已经跑出来的一致性报告
```

想自己重新跑一遍 author 步骤（需要你自己的 `cursor-agent` / `claude` / `codex` 登录态）：

```bash
examples/quickstart/scripts/run_author.sh <task_id>     # 对单个 demo task 重新生成 grader.py
python -m benchmark.tools.evaluate_bench \
  --bench-root examples/quickstart/bench \
  --produced-root examples/quickstart/produced \
  --split demo --report-dir examples/quickstart/report
```

详见 [`examples/quickstart/README.md`](examples/quickstart/README.md)。

## 仓库导航

| 路径 | 内容 |
| --- | --- |
| `CONSTITUTION.md` | 仓库宪法，25 条硬约束，任何改动先读这个 |
| `benchmark/README.md` | 自建 benchmark 的架构、数据流、D1–D3 指标定义 |
| `benchmark/tools/` | stage / self_test / validity / evaluate_bench 等工具，**零第三方依赖**，附 75 个单测 |
| `examples/quickstart/` | 6-task open-ended 端到端 demo（含真实跑出来的产物与报告） |
| `examples/quickstart/skill/` | 交付物 `verifier-author` skill 的完整独立副本 |
| `origin_data/`、`benchmark/verifier-author-bench-v1/tasks/` | 完整原始数据与物化 benchmark（体积大，**不随代码分发**，见下） |

## 数据与许可

- **代码**（`benchmark/tools/`、`examples/quickstart/skill/`、`scripts/`）以 [MIT License](LICENSE) 开源。
- **完整原始数据**（`origin_data/`，聚合自多个第三方 agent benchmark）与由其物化出的完整 `benchmark/verifier-author-bench-v1/tasks/` **不包含在本仓库分发范围内**：一是体积大（分别 5.5G / 1.7G），二是这套 benchmark 的有效性依赖"verifier-author 没见过官方评分标准"，完整公开可能被下一代模型训练吃到造成污染，三是上游多个来源的转发许可尚未逐一确认（进展见 `origin_data/SOURCES.md`）。`examples/quickstart/` 里的 6 个 demo task 是唯一随代码公开分发的数据切片，仅供跑通流程演示用。
- 如果你想复现完整 150-task benchmark，需要自行获取原始数据放入 `origin_data/`，再跑 `python -m benchmark.tools.stage`。

## 开发

```bash
pip install -r requirements.txt
python -m pytest benchmark/tools/tests -q
```
