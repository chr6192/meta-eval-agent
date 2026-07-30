# Verifier Summary: Video Transcript Extraction and Summary

## Atomic Predicates

| ID | 轨道 | 描述 | breakdown key |
|---|---|---|---|
| P1 | 确定性 | `transcript.txt` 存在且非空 | `transcript_file_exists` |
| P2 | 确定性 | 字幕稿实质内容（≥400 字符、≥5 时间戳、≥8 歌词行） | `transcript_substantive` |
| P3 | 确定性 | `video_summary.md` 存在且非空 | `summary_file_exists` |
| P4 | 确定性 | 元数据含 title / channel / duration / upload date 四字段及值 | `metadata_four_fields` |
| P5 | 确定性 | Summary 正文 200–300 词 | `summary_word_count_200_300` |
| P6 | 确定性 | ≥3 条 bullet key points | `key_points_bullets` |
| P7 | 确定性 | ≥3 个带时间戳的 notable moments | `timestamps_notable_moments` |
| P8 | 确定性 | 从 transcript 歌词词表与 summary 词表交叉验证（≥10 共享词、比率≥0.2） | `transcript_summary_alignment` |
| P9 | agentic_judge | Summary 叙述连贯、非关键词堆砌 | `agentic_judge_summary_content_quality` |
| P10 | agentic_judge | Summary 论断有 transcript 证据支撑 | `agentic_judge_summary_grounded_in_transcript` |

**分诊表**：P1–P8 必检闸门；P9–P10 仅贡献 `score`（规则 23）。

## 歧义决策 (Step 1.5)

| Amb | 选项 | 决策 | 理由 |
|---|---|---|---|
| Amb-1 | 交付物必须在 workspace 根目录 vs 允许子目录 | 递归查找同名文件，优先根目录 | Prompt 指定文件名但未禁止 agent 使用 output/ 子目录 |
| Amb-2 | Summary 字数 200–300 严格 vs 宽容 | 严格 200–300 满分；150–199 / 301–350 给 0.5 | Prompt 明示字数区间；宽容带仅用于部分信用 |
| Amb-3 | 完整字幕 vs 实质片段即可 | 实质阈值（400 字符 + 时间戳） | 任务允许不同提取工具，部分字幕仍可能合格 |
| Amb-4 | 元数据表格 vs 自由文本 | 解析字段标签 + 非空值（结构检查） | Prompt 要求四类元数据，未限定 markdown 表格 |
| Amb-5 | transcript-summary 对齐：逐句引用 vs 词表重叠 | 从 transcript 歌词派生词表，与 summary 求交集 | 合格解常 paraphrase 而非逐字引用；锚点仍来自 transcript 产物 |

## 数据来源 (规则 14)

| 信号 | 来源 |
|---|---|
| P1–P2 | workspace 产物 `transcript.txt` |
| P3–P7 | workspace 产物 `video_summary.md` |
| P8 | `transcript.txt` 歌词词表 → 对照 `video_summary.md` |
| P9–P10 | agentic_judge 读 workspace 两文件 + 可选 transcript 轨迹 |

## Gate Policy

- **gate**: `strict-deterministic`（非 pure-agentic_judge）
- **公式**: 全部 must-have（P1–P8）≥ 0.99 → `outcome_passed=True`
- **agentic_judge**: 仅影响 `score`；确定性 FAIL 时仍以 k=1 调用以保留排序信号（规则 16）
- **依据**: 任务有明确可结构校验交付物与字段；主观质量维度无法可靠关键词近似（规则 20/21）

## 心算 / 实跑预测

| Candidate | 预测 outcome | 依据 |
|---|---|---|
| qwenpaw__glm-5.1 | PASS | 两文件齐全，结构完整 |
| qwenpaw__kimi-k2.6 | PASS | 208 词 summary，结构齐全 |
| qwenpaw__qwen3.6-27b | FAIL | 无 transcript.txt / video_summary.md |
| qwenpaw__qwen3.6-35b-a3b | PASS | 完整交付 |
| qwenpaw__qwen3.6-max-preview | PASS | 完整交付 |
| qwenpaw__qwen3.6-plus | PASS | 完整交付 |
| qwenpaw__qwen3.7-max | PASS | 完整交付 |
| qwenpaw__qwen3.7-plus | PASS | 完整交付 |

**实跑（确定性层）**: PASS=7 FAIL=1。agentic_judge 层依赖本地 CLI，未阻塞闸门判定。

## 自检结果 (Step 3)

| 检查项 | 结果 |
|---|---|
| 过宽自检 | ✓ 1/8 FAIL，非全 PASS |
| 判别力自检 | ✓ 删除交付物或 stub 内容会触发 P1/P2/P3 FAIL |
| fixture 真值 | ✓ P8 词表从 transcript 产物派生，非硬编码歌词 |
| 过程信号 | ✓ 未将轨迹工具调用纳入必检项 |
| 可执行验证 | n/a 任务非可执行脚本交付 |
| agentic 关键词近似 | ✓ P9/P10 仅经 invoke_agentic_judge |
| agentic 接地 | ✓ schema 维度对应 P9/P10 |
| 回流泄漏 | ✓ 元数据/字数/对齐均结构化，仅质量维度走 judge |
| 分数拉开度 | ✓ FAIL 候选确定性全 0，PASS 候选 agentic 可区分 |
| 未读答案 | ✓ |
| 不过拟合 | ✓ grep 无候选名/视频 ID/硬编码歌词 |
| stdlib only | ✓ 仅 judge_harness 额外 import |

**反思轮数**: 2（修正 section 解析 bug；放宽 transcript-summary 对齐为词表交叉）

## Domain Note

- matched_domain: []
- inferred_domain: content-creation/video-transcript-extraction
- key_pitfalls_hit: [逐字引用对齐导致 paraphrase 合格解误杀, 仅文件存在性检查过宽]
- guide_useful: n-a
