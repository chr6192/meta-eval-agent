> Language: **English** · [中文](CONSTITUTION.zh-CN.md)

# Meta-Eval-Agent Repository Constitution

> This is the highest-authority principle for development in this repository. Any PR, iteration, or subagent work must read this document first.
> In case of conflict with lower-level documents, this file takes precedence.

---

## C1. Asset Form: Anthropic Skills Protocol (Chinese)

**Rule**: Reusable parts of meta-eval-agent must always be built as Skills; they must not be written as a one-off "collection" of `prompt + script`.

- Each skill must contain at least a `SKILL.md` (with YAML frontmatter: `name` + `description`, optionally `allowed-tools`); scripts exist as attachments, but **the interface is described by SKILL.md**.
- All skill content must be in **Chinese**, including the frontmatter's description field.
- One skill does one thing only. Combinations of multiple skills replace "giant monolithic prompts."
- Test for whether a change has been properly "skillified": can another host plug it in directly and use it? Yes → qualifies; No → it's still "script-style."

---

## C2. Physical Isolation of Train/Test Sets (No Hacking the Test Set)

**Rule**: Test-set labels and trajectories must not enter meta-eval-agent's decision loop at any point during the **entire iteration process**.

- `data_split/test.json` is a black box; only the final evaluation may open it.
- Any `eval()` / `analyze()` / `inspect()`-type operation that touches the test set must include a conspicuous assertion in the code plus a comment explaining the authorization.
- The training set is used to select hyperparameters / modify skill content / fix prompts. The test set is used for reporting, not for tuning.
- If a change only raises the training-set score while the test set drops, acknowledge it as overfitting and roll it back.

---

## C3. Physical Isolation of Ground Truth (The Verifier May Not Peek at the Answers)

**Rule**: The context seen by verifier_author **must not** contain files or directories named `gt/`, `optimal_*`, `expected_*`, `reference_*`, `solution_*`, `answer_*`, `golden_*`, `ground_truth*`, or similar.

- Isolation is enforced at the **data layer**, not merely as a "please don't look" line at the prompt layer.
- Isolation failure = the experiment is void. The first assertion in any new evaluator: scan the ctx directory, and abort if a suspected GT file is found.
- However, at runtime (the eval stage), the produced grader itself may choose whether to read these files — this is part of the grader's design freedom and is not within the scope of the isolation constraint.

---

## C4. Experimental Rigor: Reproducible, Controlled, With Generalization Checks

**Rule**: Every iteration must clearly account for "what was changed," "where it was tested," "what the control is," and "whether it overfit."

- Every iteration round must have an `iter_NN_report.md` containing at least: motivation, the changes made, the delta in training-set metrics, whether it was re-tested on the test set, and an overfitting judgment.
- Cherry-picking a favorable subset to report is not allowed. When presenting training-set accuracy, give numbers for the **full train set** or a **uniformly randomly sampled subset**.
- Any "fix for 1 task" must clearly state "whether it causes other tasks to drop in score"; a single-point fix must not be dressed up as a general improvement.

---

## C5. Report Readability: Plain and Clear, Few Abstract Terms

**Rule**: Reports must be written in plain language, without piling on empty jargon like "emergence / paradigm / anchoring / deconstruction / self-consistency."

- If one sentence can say it, don't write five.
- Key numbers (accuracy, task counts, error counts) must have concrete values; do not write "significant improvement."
- Every conclusion must be followed by 1-2 concrete examples, otherwise it doesn't count as a conclusion.
- After writing, ask yourself: could you show this directly to a data scientist or a product manager? Yes → it qualifies. If it needs "let me explain the jargon" → rewrite it.

---

## C6. Handling Failure: First Preserve Evidence, Then Analyze, Then Change

**Rule**: When an iteration round fails to achieve the expected effect, "just try changing something and see" is prohibited.

- Step 1: Record the failure cases in `analysis/iter_NN_failures.md`, listing the specific task ids and the triggering chain.
- Step 2: Cluster the failure patterns (≥3 cases counts as a "pattern"; a single point is noise).
- Step 3: Propose a change hypothesis based on the pattern, and write it into the "Hypothesis" section of the current round in `process.md`.
- Step 4: Implement the change, run one small batch (≤16 tasks), and see whether the hypothesis holds.
- Step 5: Only push to the large batch if it holds. If it doesn't hold → the hypothesis is void, go back to C6 and start over.

---

## C7. Compute Budget: Every Round Must Be Lightweight, Interruptible, and Resumable

**Rule**: A single `claude -p` call takes roughly 5-20 minutes; 80 tasks × 3 frameworks × N rounds is not unlimited.

- By default, each iteration round performs empirical validation on a **subset of 8-16 tasks**; a full-training-set evaluation is done every 5 rounds.
- **Full-set exemption**: An experiment may explicitly declare in its own `plan.md` + `process.md` that "every round runs the full train set" (rationale: comparing across rounds on the same full task set is the only true comparison — a subset introduces sampling noise and can mask trade-offs). Once declared, this exempts the experiment from the subset default in the previous bullet, but the choice, the affected rounds, and the order of magnitude of the compute budget must be recorded in `process.md`.
- Any long-running process must write to disk incrementally in jsonl, so it can resume from the point of interruption.
- (task, version) combinations that have already been run are read from cache by default, not re-run.
- Reports must honestly state "how many tasks were run in which round"; do not pass off a "representative subset N=12" as a "complete N=80."

---

## C8. Information Leakage Defense: Physical Isolation + Trajectory Forensics

**Rule**: When verifier_author writes a grader, it must never read content under the gold (answer) path.

- Layer 1 · **Staging physical isolation**: all gold is placed under `gold_verifier/`, and never enters the question layer `verifier_author_inputs/`; `self_test` uses `lib.is_gt_path` to self-check that the question layer has no residual GT (C3/C17).
- Layer 2 · **Trajectory forensics**: scan the author agent's execution trajectory (`leak_scan.scan_trajectory`) to see whether the tool calls it actually issued reached `gold_verifier/` — if it read it, that's a leak; if it didn't, it's clean. Only real actions are considered; no source-code heuristic guessing.

> Historical lesson: the old version's "static AST/grep scan of grader.py source substrings" (`answer_`/`reference_`, etc.) had an extremely high false-positive rate — it couldn't distinguish "a candidate's own answer" from "the standard answer," and has been deprecated. The only credible signal for judging leakage is "whether the agent actually read the gold."

---

## C9. Subagent Usage: Give the Specialized Work to the Specialized Agent

**Rule**: The host in this repository is a coordinator; heavy work is delegated out to subagents.

- Work that "consumes a large amount of context" — such as long-document analysis, multi-file grep, or failure clustering — should spawn an Explore or general-purpose subagent.
- Writing designs / improvement hypotheses → spawn a Plan subagent.
- Running real LLM calls → go through `claude -p`; the host does not perform grading reasoning itself.
- After a subagent returns results, the host must double-check the key numbers (don't blindly trust the summary).

---

## C10. Naming Consistency / Documentation Sync / No Dead Links

- If a document references a file path, that path must exist.
- When changing a schema field, first change the single source of truth (e.g. `CONSTITUTION.md` or `skills/.../SKILL.md`), then batch-sync downstream.
- Do not write "TODO, will fill in later"; either write it or delete it.

---

## C11. Orchestrator-loop: Supervision Signal May Only Come From Audit, Never From Oracle Peeking

**Rule**: When the principal (the orchestrator) invokes SKILL within a multi-round generate-test-audit closed loop, the **only** input permitted to be fed to the next round's skill-optimizer is the previous round's audit report (clustered failures + hypothesized root cause).

- The audit report **must not** contain the id of any task from the test set, a failure list, or a derived/official comparison.
- The audit report **must not** contain the official grader's code or a per-criterion breakdown.
- The audit report is permitted to contain: train task names, the derived vs. official PASS/FAIL binary, and failure patterns after natural-language clustering.
- Violation = the experiment is void; roll back to the last clean SKILL version and rerun.

---

## C12. Physical Separation of Roles: The optimizer / author / auditor Subagents Do Not Share Context

**Rule**: Within the orchestrated closed loop, the context of the three subagents is strictly isolated.

- skill-optimizer sees only: the current SKILL + the previous round's audit report. It **does not see** the trajectory, does not see the candidates, does not see grader.py.
- verifier-author sees only: the ctx of a single task (task_md + verifier_hints + inputs + candidates, already GT-isolated) + the current SKILL. It **does not see** the audit report, does not see the official PASS/FAIL.
- verifier-auditor sees only: the evaluator's output (derived vs. official binary) + the produced grader.py + the ctx of train tasks. It **does not see** the internal details of the SKILL, and does not write a SKILL diff.
- Any simplification of the form "I'll do the work for two roles at once" = the experiment is void.

---

## C13. SKILL Versioning and Rollback

**Rule**: A SKILL snapshot must be saved at the end of every iteration round; in-place overwriting is not allowed.

- Path: `skills/verifier-author/SKILL.md` = the currently effective version; `skills/verifier-author/_versions/v7.{N}.md` = history.
- Each round's optimizer output lands in `_versions/`, and is then promoted to `SKILL.md`.
- If any round's audit report shows **the new version regressing relative to the old version** (train strict accuracy dropping by more than **3pp** in absolute value), automatically roll back to the previous version, and mark "v{N} aborted" in `process.md`.
  - **[Tightened 2026-06-25]** Was previously 5pp; in the 260622 experiment, iter_4 regressed by 3.7pp without triggering the 5pp threshold, and the bad change (AND being too strict) persisted through v5–v8, with false_fail rising from 66 to 96 — this is the basis for this tightening.

---

## C14. The Hard Definition of "One Round of verifier_author Iteration"

**Rule**: All three of the following must be completed for it to count as one round; missing any one means it doesn't count.

1. **Change the SKILL**: land a new version at `skills/verifier-author/_versions/v{N}.md` (mandated by C13)
2. **Run the LLM with the new SKILL**: call `claude -p` to have verifier_author **regenerate** grader.py on ≥ 8 train tasks (not modify the old one)
3. **Run evaluation + compare to the previous round**: run the evaluator, compare v{N}'s Strict/Auto-only/Rank numbers against v{N-1} on the same task subset, and write it into `reports/iter_NN.md`

**What does not count as a round** (must not be numbered, must not enter iter_index as a row):

- Changing the evaluator / leak_scan / tooling scripts — labeled `tooling-NN.md`
- Writing analysis / diagnostic / failure-clustering reports — labeled `analysis-NN.md`
- Changing the SKILL but not running LLM verification — labeled `draft-vN.md` (sits in `_versions/` awaiting use, does not count toward the iter count)
- Post-processing an already-generated grader (rewriting the source via regex / AST) — see C15

**Consequence of violation**: delete the "fake round" from iter_index; add the annotation "iter_NN withdrawn (no LLM verification)" to `process.md`.

---

## C15. Post-Processing Tampering ≠ Iterating verifier_author

**Rule**: Rewriting the source of an already-generated grader via regex / AST can **only** be treated as a "ceiling-estimation experiment," and must not be treated as a result of verifier_author iteration.

- The output path for this kind of experiment must be `runs/ceiling_probes/`, **not** `runs/iters/`
- When presenting numbers in a report, they must be explicitly labeled "**ceiling probe (non LLM-loop)**"; mixing them into the same table as true-iteration numbers is prohibited
- It is not permitted to say "after NN rounds of iteration, accuracy rose from X% to Y%" if X→Y was obtained via post-processing rewrites
- Post-processing can **assist** verifier_author iteration (used to locate systematic failure patterns), but **does not replace** it

**Lesson source**: in the iter_v6 experiment, "iter_01-08 mechanical fixes to the phase2-generated grader" were labeled as 8 rounds of verifier_author iteration — this was a false count. These 8 rounds involved no LLM calls whatsoever; they were just scripts rewriting source code.

---

## C16. The LLM Call Ledger Must Be Made Public

**Rule**: Every final report must contain an "LLM call ledger" table, as the sole credible evidence for "how many true iterations this experiment performed."

Fields include:

| iter | claude -p call count | task id list | total time (seconds) | SKILL version used |
| :-: | :-: | --- | :-: | --- |

- Each row corresponds to one true verifier_author call (as defined by C14)
- The number of rows in the table = "the number of true iteration rounds"; it is **not permitted** to substitute any other denominator ("rounds in a broad sense," "rounds including the design layer," etc.)
- If a report's title mentions "N rounds of iteration," N must equal the row count of this table
- When compute does not allow enough rounds to be run, **honestly write** "performed K rounds of true LLM iteration + M ceiling probes + L draft skill versions," listing the three sets of numbers separately; do not sum them and report a single N

**Lesson source**: the iter_v6 experiment report wrote "26 rounds of iteration," but there was actually only 1 batch of LLM calls (the 8 tasks of iter_11); the other 25 items were mechanical fixes / tooling improvements / documentation analysis / draft SKILLs. The two numbers differed by a factor of 26.

---

## C17. Grading-Side Knowledge Is Invisible to verifier-author (Isolation Extended One More Layer)

**Rule**: Any "grading-side" content that **the agent cannot see while running the task, and that is only used at grading time**, must be physically isolated from verifier-author, placed in the `gold_verifier/` layer, and never in the `verifier_author_inputs/` layer.

- Objects of isolation: `## Grading Criteria`, `## LLM Judge Rubric`, `## Automated Checks` (the official grader's source code), `## Expected Behavior`, and the frontmatter's `grading_type / grading_weights`.
- verifier-author can only obtain the **input from the agent's perspective** (`## Prompt` + environment frontmatter) + **candidates** (the products of multiple harness×model explorations of the environment).
- verifier-author must **autonomously infer** the grading criteria (criteria / rubric, landed in `rubric.md`), and then write the grader based on that.
- This is an extension of C3 (GT file isolation): GT is "the answer," and the grading criteria are "the other half of the answer." Neither is permitted to enter verifier-author's input layer.

**Rationale**: feeding it the grading criteria = handing it the grading logic directly, which fails to test "whether it can, like a human annotator, work out from the artifacts alone what counts as doing it correctly."

---

## C18. gold = the Judgment of the Data's Own Built-in Verifier

**Rule**: The benchmark's gold (standard answer) is the judgment of the data's own **built-in verifier**; the goal of the generated verifier is to align with gold.

- The primary field `passed` is taken from the framework's scoring `results[].passed` (including the LLM judge dimension).
- The built-in verifier is treated as **trustworthy** (it comes from a mature benchmark); it is not questioned or redefined.
- It is **not permitted** to use the generated verifier's own output to, in turn, define or contaminate gold.

---

## C19. Evaluation Uses Multi-Dimensional Agreement, Not Just a Binary

**Rule**: Evaluating the quality of a generated verifier must report **multi-dimensional agreement**; drawing conclusions from a single `passed/failed` agreement rate alone is not permitted.

- Must include at least: D1 outcome agreement (micro + macro), D1′ false-pass / false-fail decomposition, D2 score alignment (MAE + correlation), D3 ranking agreement (discriminative power).
- **false-pass** (judging a bad candidate as passing — a missed detection) and **false-fail** (judging a good candidate as failing — a mistaken rejection) **must be tallied separately** — the two carry different costs, and mixing them into a single agreement rate will mask problems.
- Dimension definitions are in the design document §6.

---

## C20. Reachability Honesty: Distinguish "the Verifier Is Bad" From "the Task Is Out of Reach"

**Rule**: For some grading dimensions, the generated verifier is **physically unable to reach them** — because they depend on an LLM judge (aesthetics/semantics) or depend on an oracle (comparison against the gt reference solution). When reporting metrics, this portion must be kept separate from "verifier capability deficiency."

- Use `reachability.json` to annotate the dependency of each grading dimension: `workspace / transcript / llm-judgment / oracle`; `reachable = depends_on ∈ {workspace, transcript}`.
- Report both "full-dimension alignment" and "alignment within reachable dimensions." It is **not permitted** to count physically-unreachable point losses as the verifier being poorly written.
- reachability is generated by **statically parsing the official grader** (examining what files each criterion reads / what weight it carries), not by guesswork.

**Rationale**: the calendar task's `optimality_ratio` reads `gt/optimal_unscheduled.json`; once gt is isolated, no matter how good the generated grader is, it cannot replicate this — this kind of point loss should not be attributed to the verifier.

---

## C21. The Benchmark Is a Self-Contained Asset, and Must Self-Check Its Validity

**Rule**: The benchmark is materialized as a **self-contained snapshot** (portable, versionable); the grading loop **does not depend on the original data's directory structure**; GT / grading-side isolation is locked in permanently at stage time.

- The benchmark is the **underlying data asset**; the train/test split is merely a **view** on top of it, and is not bound to any single experiment.
- The benchmark **does not assume "the data is correct."** After staging, a validity self-check must be run and landed in `_stage/validity_report.md`:
  - **gold self-consistency**: rerun the official grader vs. gold agreement, listing any inconsistent tasks.
  - **discriminative power**: flag tasks that are all-pass / all-fail and thus non-discriminative.
  - **reachable weight distribution**: flag tasks whose ceiling is depressed by oracle/llm-judge.
- Correctness self-checks (GT isolation / schema / gold runnability / sampling) stand alongside the validity self-check; the benchmark is only considered usable if both pass.

---

## C22. The Deliverable Skill Must Be Bench-Agnostic and Portable to Gold-Free Production

**Rule**: The final deliverable of this experiment is a **single `verifier-author` skill** — an agent that, in an **agent data-synthesis environment with no gold to reference**, runs as an agent inside claude code / codex / cursor agent, and, relying on its own agent-loop's self-reflection, synthesizes a verifier for a task+candidates. The benchmark (gold / labels / official grading criteria / train-test split / orchestrator / auditor / optimizer) is merely **training-and-measurement scaffolding**, not part of the product. Therefore, **the deliverable skill must never have baked into it any assumption that "only holds true on the bench"** — once baked in, it will misfire or mislead once it reaches production.

- **Distinguish two categories of skill; do not mix them**:
  - **Deliverable (deployed to production, must be bench-agnostic)**: `verifier-author` only.
  - **Bench iteration machinery (training-time only, never deployed)**: `experiment-orchestrator`, `verifier-auditor`, `skill-optimizer` — their proper job is to consume gold/audit/evaluate to drive iteration, and referencing gold/official judgments is correct for them, but this dependency chain **must not** be mixed into the deliverable skill.
- **The orchestrator does not substitute for the bench in judging quality**: `experiment-orchestrator` does not build in any "acceptance gate + retry" to judge whether a verifier is good — verifier quality is determined **solely** by the benchmark's `evaluate_bench` multi-dimensional results (C19). A heuristic gate with no bench basis (e.g. a mutation kill_rate threshold) is a false signal, and is prohibited from being used as the orchestrator's quality verdict (C24). Quality improvement goes through the "audit → optimizer → full regeneration in the next round" closed loop, not a single-round built-in retry.
- **Bench-framing language prohibited in the deliverable**: phrases such as "the grading criteria are hidden from you / have been physically isolated / official rubric / official `automated.X` / official LLM Judge / aligning with official ground truth," etc. — all of these presuppose "an official standard exists, you simply can't see it." The correct framing is "**there is no ready-made grading standard; construct one autonomously from the task's intent**" (the operational behavior is exactly the same, but it does not leak the bench's measurement setup).
- **The deliverable's quality self-check must be gold-free**: any gate that depends on gold/labels/official judgments (e.g. "agreement rate with ground truth ≥ X") may only live during the bench training period, and **must not** be a built-in step of the deliverable skill. Quality assurance in production can only rely on **unsupervised proxies**: mutation/discriminative-power self-checks (the grader should flip to FAIL after the artifact is sabotaged), the rigor of self-constructed intent, and anti-leakage guardrails. Honestly acknowledge the boundary of capability — without gold, "direct verification against the truth" is lost; this is a fact, and it is not to be concealed (C5).
- **Anti-leakage guardrails are retained**: in the deliverable, "do not read the answer directory, do not hard-code answer/candidate identity" is a **general good rule for preventing overfitting**; it is harmless and beneficial in gold-free production, and is retained.
- **No decision-irrelevant noise is retained**: the deliverable skill and reader-facing documentation must not retain exploratory dimensions or dead content that "feeds into no decision" (this only adds burden for both the agent and the reader); removal decisions are carried by git history, and **no removal-note is left in the working-tree documents**.

**Rationale**: pushing up the agreement rate on the bench is not the goal; the goal is to **produce a skill that, once dropped into real, answer-free data synthesis, can still write a good grader on its own from the task's intent**. The ultimate question for judging whether the deliverable qualifies: if you drop it, unchanged, into an environment with no gold and no auditor/optimizer, can it still work independently and correctly?

**Affected**: ① (2026-06-22) removal of the D4 (criteria alignment) dimension, contraction of the satisfiability gate, and bench-agnostic-ization of "hidden official standard" wording. ② (2026-06-23) the top-level `meta-eval-agent` was renamed `experiment-orchestrator` and demoted to "training-time machinery"; its built-in acceptance gate (files/mutation) + retry were **entirely removed** — verifier quality is now determined by the bench's `evaluate_bench` verdict; the deliverable converged to a single `verifier-author` (production agent + self-reflection loop).

---

## C23. Experiment Records Are Immutable; Mechanism Changes Are Handled by Rerunning, Not by Rewriting History

**Rule**: Iteration records that have already landed on disk are an **immutable ledger of fact**, recording "what approach was used at the time and what result was obtained." When a major change occurs to the SKILL / tooling / measurement mechanism, the correct approach is to **open a new experiment and rerun** to produce new results — **never** go back and edit historical records to make them conform to the new approach.

- Immutable objects: the dated subsections of `process.md`, `reports/iter_*` reports, `_versions/` snapshots, the LLM call ledger.
- Rewriting history = both falsifying facts and creating a self-contradictory narrative (e.g. deleting a rule while leaving behind a record that says "added X for it").
- Conclusions in old records that were based on now-deprecated mechanisms are **retained as history**; if a comparison is needed, use a side-by-side "contaminated run vs. clean run," rather than erasing the old one.
- Corollary: when a change affects an existing experiment's **optimization path** (not merely its numbers), a new directory must be opened and rerun; it cannot be patched in place and continued.

**Lesson source**: after leak_scan was refactored from "static source-code scanning" to "trajectory forensics" on 2026-06-23, the choice was made to open a new experiment and do a cold-start rerun, rather than patching and continuing on top of the already-landed old experiment records; furthermore, the old-style author logs were in text format with no tool-call events, so the new mechanism was technically incapable of being retroactively applied to old rounds anyway.

---

## C24. Judgments Are Based on Factual Behavior, Not Error-Prone Heuristics; a False Signal Is Worse Than No Signal

**Rule**: Any "detection / judgment" (leakage, cheating, compliance, rollback triggers, ...) must be built primarily on **observable factual actions** (what the agent actually did, which file it read), rather than on heuristic guessing about artifact text / source code.

- **A false signal is worse than no signal**: a high-false-positive metric **contaminates the optimization path** — the optimizer chases noise, the auditor misjudges root causes, and an entire round's iteration budget is wasted. It is better to temporarily have no such signal at all than to have one that lies.
- **Rebuild from scratch, do not patch**: when a metric is found to have systematic false positives, strip it out and rebuild it (switching to a factual signal), rather than stacking more heuristics on top to suppress the false positives; and proactively examine **whether it has already contaminated existing conclusions / optimization paths** (if contaminated, rerun per C23).
- **Human-auditable, explainable**: a key judgment mechanism must be able to list its hits one by one, together with evidence, for human review (writing a review dump suffices), and the mechanism itself must be explainable in plain language (C5).

**Lesson source**: the old leak_scan statically scanned grader source substrings (`answer_`/`reference_`/`expected_`, etc.); across 3 rounds, ~99% of its 232 hits were false positives (misjudging "a candidate's own answer" or "a task's cross_reference" as reading the answer), and it also misled an entire round of iter_1's optimization (the addition of M22) into treating this noise. It was changed to `scan_trajectory`: looking only at whether the tool calls in the author's trajectory actually reached `gold_verifier/` — reading it means a leak, not reading it means clean (see C8).

---

## C25. Division of Labor Among Experiment-Directory Documents: process.md Is the Only "History-Facing" Document; Everything Else Faces Only the Present

**Rule**: Within a single experiment directory, historical narrative of the kind "what happened in the past / why it was changed this way" **is permitted to exist in only one place: `process.md`**; every other document may only describe "what things look like now, how to operate them now," and must not restate history or mention any deprecated/renamed old feature — not even with a "deprecated" annotation. Progress tracking is likewise not permitted to be manually maintained in a second copy.

- **`plan.md`** only writes **the design of this experiment's own approach, facing the future** (goals, principles, protocols, exit conditions, current asset structure). It is **prohibited** for historical narrative such as "a comparison of differences against the previous/earlier-generation experiment" or "how the starting point was inherited from the old version" to appear; the starting point is given only a single factual pointer with no historical detail (e.g. "starting-point SKILL = `v0_baseline_agenticjudge`; for inheritance provenance see `process.md`").
- **`README.md`** only holds stable reference material **facing current operation** — entry-point navigation, one-command run instructions, environment variables, orchestration conventions, manual debugging steps. It **holds no** historical narrative, explanation of differences, or old-naming cross-reference tables — this kind of content looks "stable" but is in substance "how it used to be, how it's been changed now," and belongs to the historical category, which is uniformly assigned to `process.md`.
- **`process.md`** is the **only** document in the entire experiment directory authorized to "speak toward history": before work begins, a "starting-point description" section clearly states the differences relative to the **immediately preceding experiment** (earlier generations are given only a pointer, not copied; see C23); old-feature naming/migration cross-reference tables also live here; thereafter, a factual log is appended round by round.
- **No hand-written second SOP/progress checklist**: if the orchestration script (e.g. `run_experiment.sh`) is itself an executable, resumable SOP, and `STATUS.md` is a current-state snapshot that the script auto-refreshes, then do not additionally hand-maintain a `todo.md`/checklist that restates "what has been done, what's next" — a hand-maintained document will drift out of sync with the script's actual behavior, producing a false progress record. Progress visibility recognizes only `STATUS.md` + `process.md`.
- The moment any document contains the name of a feature that has been removed/renamed (an old rule prefix, an old filename, etc.), this is judged a **C10 violation**: compliance is not achieved by "adding an annotation explaining it's deprecated" — the **entire item must be removed**, retained only in `process.md`.

**Lesson source**:
1. (2026-07-02, first occurrence) `260701_agenticjudge`'s `plan.md`/`README.md`/`process.md` each independently wrote their own explanation of "how EX1/EX2/EX3 were replaced," and these contradicted each other (the `README.md` orchestration-convention table still said "EX1/EX2/EX3 protection," while the section below it stated these three names no longer existed).
2. (2026-07-02, second occurrence — the first fix was still incomplete) the initial version of C25 mistakenly judged that an "old-naming cross-reference table" belonged in README as "stable reference" — but as long as the content is "how it used to be, how it's been changed now," it is history and should not remain in README; meanwhile, `plan.md` §5/§9 still each separately repeated the inheritance explanation for `260630_composer25`, and directly spelled out already-deprecated names such as `v0_baseline.md`/`M33–M45`/`EX1/EX2/EX3`; `todo.md` also duplicated, alongside `process.md`/`README.md`/`run_experiment.sh`, a maintained record of "what has been done / what's next." Fix: `todo.md` was deleted (`run_experiment.sh` itself is the SOP, and `STATUS.md` is already an automatic progress snapshot); the old-naming cross-reference table was moved in its entirety into `process.md`; all historical narrative and deprecated feature names in `plan.md`/`README.md` were purged entirely, leaving only a single pointer with no historical detail.

---

## Meta-Rules

- This constitution may have clauses added or removed, but every modification must simultaneously be recorded in `process.md` with the reason and the affected iteration rounds.
- The constitution does not contain "soft suggestions." Every clause is a hard constraint. Soft suggestions go in each skill's `## Known Pitfalls` or `## Change Log` section.
- **Failure lessons trigger new clauses**: every time a class of systematic false reporting is discovered (such as "fake round counts" or "ceiling estimates masquerading as true results"), a new C clause must be added to the constitution, with a "Lesson source" pointing to the specific experiment directory.
- **Simple and elegant, not over-engineered**: code, mechanisms, documentation, and the constitution itself all follow this principle — if one factual signal can solve it, don't stack four layers of heuristics on top; if two clauses can say it clearly, don't split it into five. Solve the real problem first; don't reserve architecture for imagined future needs.
