# Verifier Summary: NTIA Advisory Board Attendee List

## Step 0 · Domain

- registry 关键词未命中（无「台账」「报表」「script」等）
- 按 transcript header 逐人核对模式，参照 `office/per-record-fixture-check` 的 fixture-first 原则（未加载 guide，因未命中）

## 原子谓词表

| ID | 轨道 | 描述 | Breakdown key |
|----|------|------|---------------|
| P1 | 确定性 | attendees.md 存在且非空 | `p1_deliverable_exists` |
| P2 | 确定性 | 六类必需分区齐全 | `p2_required_sections` |
| P3 | 确定性 | header 名册 23 人全覆盖 | `p3_roster_name_coverage` |
| P4 | 确定性 | 远程/现场/官员/主席分区正确 | `p4_section_placement` |
| P5 | 确定性 | Mr. Snider 列入 Public Participants | `p5_snider_public_participant` |
| P6 | 确定性 | Summary 总人数 = fixture 重算 24 | `p6_summary_total_matches_fixture` |
| P7 | 确定性（加分） | 发言角色与 transcript 对话量一致 | `p7_speaking_role_substantive_accuracy` |

**统计**：7 条谓词（确定性 7 / agentic_judge 0）

## Step 1.5 · 歧义决策

| ID | 决策 | 理由 |
|----|------|------|
| Amb-1 | 真值取自 transcript header roster，不以对话首次自报组织为准 | Prompt 要求「as stated in the transcript」；header 是正式名册 |
| Amb-2 | Greg Rosston 不计入 Total | 主席明确其缺席，仅「可能」拨入但未发言 |
| Amb-3 | 未识别 Male Participant 不计入 Public Participants | 无法确认身份；Mr. Snider 才是 Prompt 暗示的公众参与者 |
| Amb-4 | 远程委员不得同时出现在 In-Person 分区 | Prompt 要求分入 Remote 区；* 标记为电话出席 |
| Amb-5 | Summary 总数必须精确 24，不接受 ±1 | 名册人数客观可重算，宽阈值会放过多计一人 |

## Gate Policy

- **gate**：`strict-deterministic`（规则 15）
- **公式**：全部 6 条 must-have `>= 0.99` → `outcome_passed=True`
- **score**：7 条谓词算术平均（含加分项），与闸门独立
- **无 agentic_judge**：发言角色可从 transcript 说话标签与篇幅结构化推导

## 数据来源自检

| 谓词 | 输入 | 产物 |
|------|------|------|
| P1–P7 | `meeting-transcript.md` | `attendees.md` |

候选 workspace 中均存在 `meeting-transcript.md` 与 `attendees.md`（已抽检）。

## 心算 / 实跑预测（8 candidates）

| Candidate | 预测 | 实际 | 主要差异 |
|-----------|------|------|----------|
| qwen3.7-max | PASS | PASS | — |
| qwen3.7-plus | PASS | PASS | — |
| qwen3.6-plus | PASS | PASS | — |
| qwen3.6-max-preview | PASS | PASS | — |
| glm-5.1 | PASS | PASS | — |
| kimi-k2.6 | PASS | PASS | 组织名笔误但未触发分区/名册闸门 |
| qwen3.6-27b | FAIL | FAIL | 远程委员误入 In-Person 区；Total=25 |
| qwen3.6-35b-a3b | FAIL | FAIL | 缺 Snider，以未识别来电者顶替 |

**分布**：PASS=6 FAIL=2；score 极差 max(PASS)−min(FAIL)=1.0−0.714=0.286

## Step 3 · 自检

| 项 | 结果 |
|----|------|
| 过宽 | ✓ 2/8 FAIL，非全 PASS |
| 判别力 | ✓ 删 attendees.md → P1=0 |
| fixture 真值 | ✓ 名册/人数/远程标记均从 meeting-transcript.md 解析 |
| 过程信号 | ✓ 未用 transcript 轨迹 |
| 可执行验证 | n/a |
| agentic_judge | n/a（未使用） |
| 分数拉开度 | ✓ 0.286 ≥ 0.25 |
| 反泄漏 | ✓ 无候选名/ gold 路径硬编码 |
| stdlib only | ✓ 仅 os/re/typing |
| 谓词不变量 | ✓ p3 满分且 p4<0.5 时强制 p4=0 |

**反思轮数**：2（收紧分区互斥、修复短别名误匹配）

## 产物

- `grader.py`
- `rubric.md`
- `verifier_summary.md`（无 `judge_harness.py`）

## Domain Note

- matched_domain: []
- inferred_domain: office/meeting-transcript-extraction
- key_pitfalls_hit: [短别名子串误命中（dan→Stancil 误判在 In-Person 区）, 远程委员双列入 In-Person+Remote 区, 公众参与者与未识别来电混淆, Summary 多计一人]
- guide_useful: n-a
