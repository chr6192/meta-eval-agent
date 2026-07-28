#!/bin/bash
# 对 examples/quickstart/bench 里的一个 demo task，用你自己的 agent CLI
# （cursor-agent / claude / codex 任一，需要你自己先登录好）重新跑一遍
# verifier-author，把产出写回 examples/quickstart/produced/<task_id>/。
#
# 用法：./run_author.sh <task_id> [model] [agent_cmd]
#   ./run_author.sh T003zh_calendar_scheduling composer-2.5 cursor-agent
#   ./run_author.sh T012_expense_report sonnet-4.6-thinking claude
#
# 隔离设计（与本仓库训练期实验一致，见 CONSTITUTION.md C3/C8/C17）：
# author 在一个只含 skill + 该 task「考题」（verifier_author_inputs/）的临时沙箱里跑，
# 物理上访问不到 gold_verifier/（官方评分标准/参考答案）。
#
# 沙箱位置：仓库内 examples/quickstart/.sandbox/（已加入 .gitignore，不提交），
# 不用系统 /tmp —— 避免依赖系统临时目录（部分环境 /tmp 受限/易被清理/不可控），
# 保证「跑一次 demo」全程留在仓库自己的目录树里，运行结束自动清理。
set -euo pipefail
TID="${1:?usage: $0 <task_id> [model] [agent_cmd]}"
MODEL="${2:-composer-2.5}"
AGENT_CMD="${3:-cursor-agent}"

HERE="$(cd "$(dirname "$0")" && pwd)"
QROOT="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$QROOT/../.." && pwd)"

INPUTS="$QROOT/bench/tasks/$TID/verifier_author_inputs"
SKILL_SRC="$QROOT/skill"
OUTDIR="$QROOT/produced/$TID"

[ -d "$INPUTS" ] || { echo "[err] 找不到 task 考题层：$INPUTS（task_id 拼错了？）" >&2; exit 1; }

SANDBOX_ROOT="$QROOT/.sandbox"
mkdir -p "$SANDBOX_ROOT"
SANDBOX="$(mktemp -d "$SANDBOX_ROOT/${TID}.XXXXXX")"
trap 'rm -rf "$SANDBOX"' EXIT
cp -R "$INPUTS" "$SANDBOX/verifier_author_inputs"
cp -R "$SKILL_SRC" "$SANDBOX/skill"
mkdir -p "$SANDBOX/produced" "$OUTDIR"

PROMPT="你是 verifier-author agent。工作目录就是当前目录（一个只含本任务考题的隔离沙箱），
所有路径相对当前目录，绝不访问当前目录之外的任何路径（这里没有任何标准答案文件）。

先完整读 ./skill/SKILL.md，按需加载 ./skill/meta-rules.md 与 ./skill/domain-strategy.md。
严格按顺序执行 Step 0 domain 识别 → Step 1 Decompose → Step 1.5 歧义外显 → Step 2 Encode → Step 3 Self-reflection。

唯一输入：./verifier_author_inputs/（task_md.md + inputs/ + candidates/<harness>__<model>/{workspace/, transcript.jsonl}）。

产出写到 ./produced/：grader.py（签名 def grade(transcript, workspace_path) -> dict，只许 import 标准库）、
rubric.md、verifier_summary.md。完成后回复 ≤200 字自验摘要。"

echo "[author] task_id=$TID model=$MODEL agent=$AGENT_CMD (sandbox=$SANDBOX)"
TIMEOUT_SECS="${TIMEOUT_SECS:-1200}"
( cd "$SANDBOX" && "$AGENT_CMD" -p --force --trust --model "$MODEL" --output-format stream-json "$PROMPT" ) &
PID=$!
( sleep "$TIMEOUT_SECS"; kill -9 "$PID" 2>/dev/null ) &
WD=$!
wait "$PID" 2>/dev/null || true
kill -9 "$WD" 2>/dev/null || true

for f in grader.py rubric.md verifier_summary.md; do
  [ -f "$SANDBOX/produced/$f" ] && cp "$SANDBOX/produced/$f" "$OUTDIR/$f"
done

if [ -f "$OUTDIR/grader.py" ]; then
  echo "[author] 完成 -> $OUTDIR"
else
  echo "[author] 未产出 grader.py，检查 $AGENT_CMD 是否已登录/模型名是否有效" >&2
  exit 1
fi
