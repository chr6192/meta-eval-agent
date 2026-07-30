> Language: **English** · [中文](README.zh-CN.md)

# meta-eval-agent

**In one sentence**: use an agent (`verifier-author`) in place of a human annotator — in settings with no ground truth and no rubric, given "a task + several candidate solution transcripts", automatically write a grading program (`grader.py`) that can output a PASS/FAIL verdict. This repository is the public record of the methodology + self-built benchmark built around this agent.

## What problem this solves

Agent data synthesis / RL training frequently needs to score "whether a given agent task was done correctly", but many tasks **have no ready-made grading script** — the traditional approach is to have a human annotator write a verifier by hand based on the task intent, which is costly and hard to scale. `verifier-author` lets an LLM agent do this itself: it is given only the task's `## Prompt` and a handful of candidate solution transcripts (workspace artifacts + execution traces); the grading criteria and the ground truth are **physically invisible to it**. It must infer on its own "what counts as doing it correctly", encode that into a grading program, and, within its own agent-loop, converge on a reliable verifier through self-reflection (over-broad-criteria self-checks, discriminative-power self-checks, cross-checking against fixture ground truth, etc.).

## Three-layer structure

```
CONSTITUTION.md              Repository constitution: 25 hard constraints (data isolation / anti-leakage /
                              experiment honesty / version rollback / ...)
        │
        ▼
benchmark/                   Self-built benchmark: turns "task + candidate transcripts + official judgments"
                              into an exam that measures the agreement between the grader the agent writes
                              and the official judgments (multi-dimensional D1–D3 metrics)
        │
        ▼
Training-time scaffolding (for internal iteration only, not distributed with the code):
                              an orchestration loop with three isolated roles — author/auditor/optimizer —
                              used to iteratively refine the verifier-author skill
        │
        ▼
Deliverable: the verifier-author skill (see `examples/quickstart/skill/SKILL.md`)
                              — bench-agnostic, can be dropped directly into claude code / codex / cursor
                              agent for production use
```

The `experiment-orchestrator`/`verifier-auditor`/`skill-optimizer` in `benchmark/` and the training-time scaffolding are **purely measurement scaffolding used during training**; they never ship as part of the deliverable. The sole deliverable is the single skill `verifier-author` (see `CONSTITUTION.md` C22).

## Run an end-to-end example in 30 seconds

You don't need the full raw dataset to try this out — `examples/quickstart/` already ships with 6 real, open-ended tasks (no single canonical answer) covering blog writing / contract legal analysis / meeting-minutes extraction x2 / video transcript summarization / issue triage, and the full `author → evaluate` pipeline has already been run once on them with a real LLM agent, with the outputs and report checked in:

```bash
cd examples/quickstart
cat report/eval_report.md          # view the already-generated agreement report
```

To re-run the author step yourself (requires your own `cursor-agent` / `claude` / `codex` login session):

```bash
examples/quickstart/scripts/run_author.sh <task_id>     # regenerate grader.py for a single demo task
python -m benchmark.tools.evaluate_bench \
  --bench-root examples/quickstart/bench \
  --produced-root examples/quickstart/produced \
  --split demo --report-dir examples/quickstart/report
```

See [`examples/quickstart/README.md`](examples/quickstart/README.md) for details.

## Repository navigation

| Path | Contents |
| --- | --- |
| `CONSTITUTION.md` | The repository constitution — 25 hard constraints; read this first before making any changes |
| `benchmark/README.md` | Architecture, data flow, and D1–D3 metric definitions for the self-built benchmark |
| `benchmark/tools/` | Tools such as stage / self_test / validity / evaluate_bench — **zero third-party dependencies**, with 75 unit tests |
| `examples/quickstart/` | A 6-task, open-ended, end-to-end demo (including real generated artifacts and reports) |
| `examples/quickstart/skill/` | A complete, standalone copy of the deliverable `verifier-author` skill |
| `origin_data/`, `benchmark/verifier-author-bench-v1/tasks/` | The full raw data and materialized benchmark (large, **not distributed with the code**, see below) |
| README | This README is also available in Chinese: [`README.zh-CN.md`](README.zh-CN.md) |

## Data and licensing

- **Code** (`benchmark/tools/`, `examples/quickstart/skill/`, `scripts/`) is open-sourced under the [MIT License](LICENSE).
- The **full raw data** (`origin_data/`, aggregated from several third-party agent benchmarks) and the full `benchmark/verifier-author-bench-v1/tasks/` materialized from it **are not included in this repository's distribution**, for three reasons: first, their size (5.5G and 1.7G respectively); second, the validity of this benchmark depends on "verifier-author never having seen the official grading criteria", and full public release could be ingested into next-generation model training and cause contamination; third, the redistribution licenses of several upstream sources have not yet been individually confirmed (see `origin_data/SOURCES.md` for progress). The 6 demo tasks in `examples/quickstart/` are the only data slice distributed publicly with the code, intended solely for demonstrating the pipeline.
- If you want to reproduce the full 150-task benchmark, you'll need to obtain the raw data yourself, place it in `origin_data/`, and then run `python -m benchmark.tools.stage`.

## Development

```bash
pip install -r requirements.txt
python -m pytest benchmark/tools/tests -q
```
