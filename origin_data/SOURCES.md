# 原始数据来源说明（TODO：逐条确认授权状态）

## PawBench 上游

本仓库 `origin_data/` 下的完整原始数据**直接来自 PawBench v1.0**——一套 agent 任务评测框架，用于在统一 harness 下跑多模型、对 workspace 产物与执行轨迹做混合判分（确定性 `## Automated Checks` + `## Grading Criteria` + `## LLM Judge Rubric`）。`verifier-author-bench-v1` 的 gold 层（`official_grader.py`、`labels.json`、`official_rubric.md`）均派生自 PawBench 自带的 built-in verifier 与 framework 跑分结果；本仓库**不分发** PawBench 原始数据，仅保留此说明文档（见根目录 `.gitignore`）。

### 目录结构

```
origin_data/
├── pawbench-v1.0/              # PawBench 任务包（本仓库 stage 的直接输入）
│   ├── tasks/                  # 150 个 task，每个为单个 .md（frontmatter + Prompt + 评分段）
│   └── assets/                 # 各 task 的 baseline / fixture 文件
└── 20260615_111519/            # 一次 PawBench 跑分快照（run_id，见 benchmark/tools/paths.py）
    └── pawbench/
        └── <model>/            # 8 个模型：glm-5.1, kimi-k2.6, qwen3.6-*, qwen3.7-*
            └── qwenpaw/        # 当前候选矩阵使用的 harness
                ├── *.json      # framework 跑分：每 task 的 passed/score/breakdown（→ gold labels.json）
                ├── workspaces/ # 各 task 的 end-state 快照（→ candidates/*/workspace/）
                └── transcripts/# 各 task 的完整对话轨迹（→ candidates/*/transcript.jsonl）
```

### PawBench 任务包内容（每个 `tasks/T###_<来源>_<id>.md`）

| 段落 / 字段 | 用途 | 进入 verifier-author-bench 的哪一层 |
| --- | --- | --- |
| frontmatter（`grading_type`、`workspace_files` 等） | 任务元数据与环境配置 | 考题层（去 GT 后） |
| `## Prompt` | agent 可见的任务描述 | 考题层 `task_md.md` |
| `## Expected Behavior` / `## Grading Criteria` / `## LLM Judge Rubric` | 人工撰写的评分标准 | **答案层** `official_rubric.md`（对 author 隐藏） |
| `## Automated Checks`（Python `grade()`） | 确定性批改程序 | **答案层** `official_grader.py` |
| framework `*.json` 的 `results[]` | 含 LLM judge 在内的最终 passed/score | **答案层** `labels.json` |

`grading_type` 分布（150 task）：`automated` / `hybrid` / `llm_judge` 三类均有；hybrid 与 llm_judge 占多数，是 verifier-author 难度设定的主要来源（需自主归纳主观评分维度）。

### 与下游 benchmark 的关系

```
PawBench v1.0（origin_data/）
        │  python -m benchmark.tools.stage
        ▼
verifier-author-bench-v1/     # 物化快照：考题层与答案层物理隔离
        │  verifier-author agent + evaluate_bench
        ▼
produced/<task>/grader.py     # 被考核者产出的判分程序
```

本地复现：将 PawBench 原始数据放入 `origin_data/` 后执行 `python -m benchmark.tools.stage`（路径常量见 `benchmark/tools/paths.py`）。`examples/quickstart/` 中的 6 个 demo task 是从完整 150 task 中精选、已物化的小切片，不代表 PawBench 全集已获公开分发许可。

---

## PawBench 内的 6 个子来源（合并前）

`pawbench-v1.0/tasks/` 里的 150 个 task **在并入 PawBench 之前**按文件名前缀来自以下 6 个独立 benchmark / 任务库。下表记录的是**更上游**的来源拆分；PawBench 本身是对它们的统一封装与跑分框架。在**决定要不要/怎么公开分发这批数据**之前，需要把"来自哪里、能不能转发"逐条记清楚——目前状态是**尚未逐一核实**，公开发布完整数据集前必须补完这张表。

| 前缀 | task 数 | 说明 | 授权/许可状态 |
| --- | --- | --- | --- |
| `claweval` | 52 | 待补充：来源项目名称、版本、获取渠道 | 待确认 |
| `qwenclawbench` | 29 | 待补充 | 待确认 |
| `qwenpawbench` | 21 | 待补充 | 待确认 |
| `pinchbench` | 23 | 待补充 | 待确认 |
| `skillsbench` | 15 | 待补充（内部调研笔记未随代码公开分发） | 待确认 |
| `wildclawbench` | 10 | 待补充 | 待确认 |

## 为什么这件事不能跳过

1. **转发许可**：即便原始来源本身可公开访问，把它们转换（去评分标准/去 GT）后再打包重新分发，是否在原始 license 允许范围内，需要逐个来源确认。
2. **Contamination（污染）风险**：这套 benchmark 的有效性依赖"verifier-author 没见过官方评分标准"；完整公开 150 题+官方 grader+8 模型答卷，等于把"题+答案"一起交给了下一代模型的训练语料，benchmark 会失效。
3. **`benchmark/verifier-author-bench-v1/tasks/`**（物化产物，已在 `.gitignore` 里）继承上述两个问题，同样不能未经确认就整体公开。

## 当前的临时方案

- `examples/quickstart/` 只公开了 6 个精选 task 的物化产物（含官方 grader/labels），作为"跑通流程"的演示切片，不代表已解决上述许可问题——这 6 个是从体量、内容对公开演示相对友好的角度选的，**不等于**已确认其上游许可允许长期公开分发。
- 完整数据集想复现的人，需要自行获取 **PawBench v1.0 原始数据**（任务包 `pawbench-v1.0/` + 跑分快照 `20260615_111519/`，或等价物），放入 `origin_data/`，再跑 `python -m benchmark.tools.stage` 本地重建 `benchmark/verifier-author-bench-v1/`。若只有 6 个子来源的原始 task 而未经 PawBench 统一封装与跑分，还需自行补齐 harness 跑分与 built-in verifier 管线。

## TODO

- [ ] 逐个来源确认：全称、公开链接、license 条款、是否允许转发衍生数据
- [ ] 确认后决定：完整数据是否可以对外提供下载（自建对象存储 / Zenodo 等，不用 HuggingFace）
- [ ] 若某来源不允许转发，evaluate 该来源 task 时改为"仅提供 task_id 索引，用户自行获取原始内容"的方案
