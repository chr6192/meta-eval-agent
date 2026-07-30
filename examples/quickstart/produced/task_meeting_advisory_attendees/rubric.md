# Rubric: CSMAC Meeting Attendee List

任务要求从 `meeting-transcript.md` 提取结构化出席者清单，写入 `attendees.md`，并按指定分区与字段组织。

## 评分说明

- **闸门（PASS/FAIL）**：全部 must-have 谓词得分 ≥ 0.99。
- **连续分（score）**：全部谓词（含加分项）的算术平均，用于候选间排序。

## Criteria

| Key | Must-have | 权重 | 说明 |
|-----|-----------|------|------|
| `p1_deliverable_exists` | 是 | 闸门 | `attendees.md` 存在且正文 ≥200 字符 |
| `p2_required_sections` | 是 | 闸门 | 含 Leadership / In-Person / Remote / Officials / Public / Summary 六类分区 |
| `p3_roster_name_coverage` | 是 | 闸门 | 会议记录 header 名册中每人（主席、委员、官员）均在产物中出现 |
| `p4_section_placement` | 是 | 闸门 | 远程委员仅在 Remote 区、现场委员仅在 In-Person 区、主席在 Leadership、官员在 Officials |
| `p5_snider_public_participant` | 是 | 闸门 | Mr. Snider 列在 Public Participants 分区（会议末尾发言的公众） |
| `p6_summary_total_matches_fixture` | 是 | 闸门 | Summary 总人数与从 transcript 重算的 24 人一致（不含缺席的 Greg Rosston） |
| `p7_speaking_role_substantive_accuracy` | 否 | 加分 | 有实质发言者与仅自我介绍者在 Speaking Role 字段分类正确 |

## 三档示例（代表性）

### p3_roster_name_coverage
- **1.0**：23 名 header 名册人员全部可定位
- **0.5**：≥80% 出现
- **0.0**：<80%

### p4_section_placement
- **1.0**：全部人员分区正确，远程委员未重复列入 In-Person 区
- **0.8–0.98**：绝大多数正确（按比例计分，但 <0.99 仍 FAIL 闸门）
- **0.0**：<80% 正确

### p5_snider_public_participant
- **1.0**：Snider 出现在 Public Participants 表格/列表中
- **0.0**：缺失或仅在脚注/缺席区提及

### p6_summary_total_matches_fixture
- **1.0**：Summary 表 Total = 24
- **0.0**：总数错误（如将未确认公众或缺席者计入导致 25）

### p7_speaking_role_substantive_accuracy
- **1.0**：≥90% 发言角色与 transcript 对话量一致
- **0.5**：75–89%
- **0.0**：<75%

## 数据来源

| 用途 | 路径 |
|------|------|
| 名册真值 | `{workspace}/meeting-transcript.md` header（`## Contents` 之前） |
| 发言角色真值 | `{workspace}/meeting-transcript.md` 对话正文 |
| 判分产物 | `{workspace}/attendees.md`（或 `output/attendees.md`） |
