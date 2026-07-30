> Language: **English** · [中文](SOURCES.zh-CN.md)

# Raw Data Source Notes (TODO: confirm authorization status item by item)

## PawBench Upstream

The complete raw data under `origin_data/` in this repo **comes directly from PawBench v1.0** — an agent task evaluation framework used to run multiple models under a unified harness and perform hybrid grading of workspace artifacts and execution trajectories (deterministic `## Automated Checks` + `## Grading Criteria` + `## LLM Judge Rubric`). The gold layer of `verifier-author-bench-v1` (`official_grader.py`, `labels.json`, `official_rubric.md`) is entirely derived from PawBench's own built-in verifier and framework scoring results. This repo **does not distribute** PawBench's raw data; only this documentation is kept (see the root `.gitignore`).

### Directory Structure

```
origin_data/
├── pawbench-v1.0/              # PawBench task package (direct input for this repo's staging)
│   ├── tasks/                  # 150 tasks, each a single .md (frontmatter + Prompt + grading sections)
│   └── assets/                 # baseline / fixture files for each task
└── 20260615_111519/            # a PawBench scoring snapshot (run_id, see benchmark/tools/paths.py)
    └── pawbench/
        └── <model>/            # 8 models: glm-5.1, kimi-k2.6, qwen3.6-*, qwen3.7-*
            └── qwenpaw/        # harness used by the current candidate matrix
                ├── *.json      # framework scoring: passed/score/breakdown per task (→ gold labels.json)
                ├── workspaces/ # end-state snapshot per task (→ candidates/*/workspace/)
                └── transcripts/# full conversation trajectory per task (→ candidates/*/transcript.jsonl)
```

### PawBench Task Package Contents (each `tasks/T###_<source>_<id>.md`)

| Section / Field | Purpose | Which layer of verifier-author-bench it becomes |
| --- | --- | --- |
| frontmatter (`grading_type`, `workspace_files`, etc.) | Task metadata and environment configuration | Question layer (after GT removal) |
| `## Prompt` | Task description visible to the agent | Question layer, `task_md.md` |
| `## Expected Behavior` / `## Grading Criteria` / `## LLM Judge Rubric` | Human-written grading standards | **Answer layer**, `official_rubric.md` (hidden from the author) |
| `## Automated Checks` (Python `grade()`) | Deterministic grading program | **Answer layer**, `official_grader.py` |
| `results[]` from the framework `*.json` | Final passed/score, including the LLM judge | **Answer layer**, `labels.json` |

`grading_type` distribution (150 tasks): all three of `automated` / `hybrid` / `llm_judge` are present; `hybrid` and `llm_judge` make up the majority and are the main source of difficulty for verifier-author (requiring it to independently induce subjective scoring dimensions).

### Relationship to the Downstream Benchmark

```
PawBench v1.0 (origin_data/)
        │  python -m benchmark.tools.stage
        ▼
verifier-author-bench-v1/     # materialized snapshot: question layer and answer layer physically isolated
        │  verifier-author agent + evaluate_bench
        ▼
produced/<task>/grader.py     # grading program produced by the party being evaluated
```

Local reproduction: place the PawBench raw data into `origin_data/` and run `python -m benchmark.tools.stage` (path constants are in `benchmark/tools/paths.py`). The 6 demo tasks in `examples/quickstart/` are a curated, already-materialized small slice of the full 150 tasks, and do not imply that the full PawBench set has been cleared for public distribution.

---

## The 6 Sub-Sources Within PawBench (Before Merging)

The 150 tasks in `pawbench-v1.0/tasks/`, **before being merged into PawBench**, came from the following 6 independent benchmarks / task libraries, identified by filename prefix. The table below records the **further-upstream** source breakdown; PawBench itself is a unified wrapper and scoring framework over them. Before **deciding whether/how to publicly distribute this data**, we need to clearly record, source by source, "where it came from" and "whether it can be redistributed" — the current status is that **this has not yet been verified item by item**, and this table must be completed before the full dataset can be publicly released.

| Prefix | Task Count | Notes | Authorization/License Status |
| --- | --- | --- | --- |
| `claweval` | 52 | TBD: source project name, version, acquisition channel | Pending confirmation |
| `qwenclawbench` | 29 | TBD | Pending confirmation |
| `qwenpawbench` | 21 | TBD | Pending confirmation |
| `pinchbench` | 23 | TBD | Pending confirmation |
| `skillsbench` | 15 | TBD (internal research notes were not distributed publicly with the code) | Pending confirmation |
| `wildclawbench` | 10 | TBD | Pending confirmation |

## Why This Cannot Be Skipped

1. **Redistribution license**: even if the original sources are themselves publicly accessible, whether repackaging and redistributing them after transformation (removing grading standards/GT) falls within the scope allowed by the original license needs to be confirmed source by source.
2. **Contamination risk**: the validity of this benchmark depends on "verifier-author having never seen the official grading standards"; publicly releasing all 150 questions + official graders + 8 models' answer submissions in full would hand "questions and answers" together to the next generation of models' training corpora, invalidating the benchmark.
3. **`benchmark/verifier-author-bench-v1/tasks/`** (the materialized artifact, already in `.gitignore`) inherits both problems above and likewise cannot be released in full without confirmation.

## Current Interim Approach

- `examples/quickstart/` only publishes the materialized artifacts (including official grader/labels) for 6 curated tasks, as a demo slice for "getting the pipeline running" — this does not mean the licensing issues above have been resolved. These 6 were chosen for being relatively demo-friendly in size and content, which **does not mean** their upstream licenses have been confirmed to permit long-term public distribution.
- Anyone who wants to reproduce the full dataset needs to obtain the **PawBench v1.0 raw data** themselves (the task package `pawbench-v1.0/` + the scoring snapshot `20260615_111519/`, or equivalent), place it in `origin_data/`, and run `python -m benchmark.tools.stage` to locally rebuild `benchmark/verifier-author-bench-v1/`. If you only have the raw tasks from the 6 sub-sources without PawBench's unified wrapping and scoring, you will also need to fill in the harness scoring and built-in verifier pipeline yourself.

## TODO

- [ ] Confirm each source individually: full name, public link, license terms, whether redistribution of derived data is permitted
- [ ] After confirmation, decide: whether the full dataset can be made available for download externally (self-hosted object storage / Zenodo, etc., not HuggingFace)
- [ ] If a given source does not permit redistribution, switch to a "provide only the task_id index; users obtain the raw content themselves" approach when evaluating tasks from that source
