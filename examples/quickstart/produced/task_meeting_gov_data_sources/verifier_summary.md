# Verifier Summary: NASA UAP Hearing Data Sources Extraction

## Step 0 · Domain Identification

- **matched_domain**: `[]`（registry 关键词未命中；任务为会议转录信息抽取，非既有 domain 模板）
- **inferred_domain**: `office/meeting-transcript-extraction`
- **layer_hint applied**: 参照 `office/per-record-fixture-check` 思路——从 workspace 输入（transcript.md）派生逐条锚点再与产物对照，但无独立 fixture 文件

## Atomic Predicates

| ID | 谓词 | 轨道 | 闸门 |
|----|------|------|------|
| P1 | `data_sources.md` 存在且非空（>200 字符） | 确定性 | must-have |
| P2 | 顶部含 category + owner/operator 列的 summary table | 确定性 | must-have |
| P3 | 六个 Prompt 要求类别全部出现 | 确定性 | must-have |
| P4 | 每条数据源含 Owner/Description/Relevance/Limitations/Who-referenced 字段标签 | 确定性 | must-have |
| P5 | 从 transcript.md 派生的数据源锚点覆盖率 ≥85% | 确定性 | must-have |
| P6 | 内容非退化（无重复堆砌、有足够 detail section） | 确定性 | must-have |
| P7 | 独立数据源条目数 ≥15 | 确定性 | nice-to-have |

**分诊统计**: 7 条确定性 / 0 条 agentic_judge

## Step 1.5 · 歧义决策

| Amb | 解读点 | 选择 | 理由 |
|-----|--------|------|------|
| Amb-1 | 数据源粒度：每个传感器型号 vs 合并为"DOD sensors" | 锚点级（型号/系统名在 transcript 中出现即要求覆盖） | Prompt 要求提取会议中引用的各系统；合并类条目可算覆盖 DOD 锚点但 MQ-9/P-3/F-35 等必须独立出现 |
| Amb-2 | 类别名是否必须精确匹配 Prompt 原文 | 宽松别名匹配（如 "Government/Military" 变体） | 候选常用斜杠/空格变体；语义等价即可 |
| Amb-3 | 覆盖率满分阈值 | 85%（非 100%） | 会议中部分系统以口语泛指出现，合理合并条目可覆盖；100% 会错杀格式正确但合并同义词的解 |
| Amb-4 | 是否要求读 transcript 轨迹 | 否（只查产物内容） | 规则 18：过程信号不进闸；Prompt 未要求展示阅读轨迹 |
| Amb-5 | 提议/未来系统（如 crowdsourcing platform proposed）是否必含 | 仅当 transcript 有 crowdsourc/iPhone 锚点时要求 | 锚点派生原则：transcript 未明确提及的不硬编码 |

## Data Sources (Rule 14)

| 信号 | 数据来源 |
|------|----------|
| P1–P7 产物检查 | `workspace_path/data_sources.md` 或 `output/data_sources.md` |
| P5 锚点派生 | `workspace_path/transcript.md` |

自检：两份路径在 `verifier_author_inputs/inputs/` 与候选 workspace 中均存在。

## Gate Policy

- **gate**: `deterministic-all-must-have`
- **formula**: `outcome_passed = all(p1..p6 >= 0.99)`
- **score**: `p7` 均值（gate 失败时 capped ≤0.49）
- **理由**: 任务有明确结构化交付物与可从 transcript 派生的客观锚点，不适用纯 agentic_judge 闸门

## 交叉谓词不变量

- P1 失败 → P2–P6 capped 0.5
- P6 退化内容 → P5 capped 0.5

## Self-Reflection

### 轮次 1 · 实跑分布（8 候选）

| 候选 | outcome | score |
|------|---------|-------|
| qwen3.7-max | PASS | 1.0 |
| qwen3.7-plus | PASS | 1.0 |
| qwen3.6-max-preview | PASS | 1.0 |
| qwen3.6-plus | PASS | 1.0 |
| qwen3.6-27b | PASS | 1.0 |
| glm-5.1 | PASS | 1.0 |
| kimi-k2.6 | PASS | 1.0 |
| qwen3.6-35b-a3b | FAIL | 0.0 |

PASS=7 / FAIL=1；分数极差 1.0（≥0.25 ✓）

### 自检清单

| 项 | 结果 |
|----|------|
| 过宽（全 PASS） | ✓ 1/8 FAIL |
| 判别力（破坏测试） | ✓ 删 deliverable → p1=0, gate FAIL |
| fixture 真值 | ✓ P5 锚点从 transcript.md 动态派生 |
| 过程信号 | ✓ 未用 transcript 轨迹 |
| 可执行验证 | n/a |
| agentic_judge | n/a（未使用） |
| 分数拉开度 | ✓ 1.0 vs 0.0 |
| 反例可抓 | ✓ 35b-a3b 重复堆砌被 P6/P5 捕获 |
| 不过拟合 | ✓ 无候选名字面量 |
| stdlib only | ✓ |

### 反例标注

- P1: 空文件 / 仅标题
- P5: 只写 DOD 一条漏掉 MQ-9、FAA、data.nasa.gov
- P6: 单表行无限重复 "primary defense"（实际候选 35b-a3b）

## Domain Note

- matched_domain: []
- inferred_domain: office/meeting-transcript-extraction
- key_pitfalls_hit: ["直接在产物文本上做整体比例判断而不从 transcript 派生锚点（已通过 _derive_expected_sources 避免）", "用关键词 OR 判断覆盖而不与 transcript 锚点对照"]
- guide_useful: n-a
