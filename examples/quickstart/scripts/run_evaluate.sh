#!/bin/bash
# 对 examples/quickstart/produced/ 里已生成的 grader，跑一遍阅卷，产出报告。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
QROOT="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$QROOT/../.." && pwd)"

cd "$REPO"
python3 -m benchmark.tools.evaluate_bench \
  --bench-root "$QROOT/bench" \
  --produced-root "$QROOT/produced" \
  --split demo \
  --report-dir "$QROOT/report"

echo
echo "报告已写到 $QROOT/report/eval_report.md"
