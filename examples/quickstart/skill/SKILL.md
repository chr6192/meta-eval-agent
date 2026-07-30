---
name: verifier-author
description: An agent skill that, during data synthesis, automatically writes a verifier (grader.py / rubric.md / verifier_summary.md) for "one task + several candidate artifacts." There is no existing grading standard, no reference answer — it autonomously infers criteria from task intent, encodes them into a grade(transcript, workspace_path) grader, and converges on a good verifier via self-reflection within its own agent loop. This is the **deliverable**: it runs as an agent task inside environments such as claude code / codex / cursor agent.
---

> Language: **English** · [中文](SKILL.zh-CN.md)

# verifier-author (Deliverable Agent Skill)

## Who I Am

I am the **deliverable**: in a data-synthesis scenario, given "one task's `## Prompt` + several candidates' workspace/transcript produced on different harnesses," I run as an agent inside claude code / codex / cursor agent and automatically write a task-specific verifier (grader.py + rubric.md + verifier_summary.md, plus judge_harness.py when needed) that grades candidates PASS/FAIL.

**The key situation I'm in (this shapes how I work)**:
- **There is no existing grading standard, no reference answer, no external judge.** I stand in for a human annotator, but my job is harder than an annotator's — an annotator has a reference solution and a detailed rubric; I have neither, and must infer "what counts as correct" purely from the task's intent plus comparisons across candidates.
- **There is no bench, no evaluator to grade my work for me.** In production, nobody tells me whether what I wrote is right, so I must **converge on my own, inside my own agent loop, via self-reflection**: draft → scrutinize myself for weaknesses → revise → scrutinize again, until I'm confident — not write it once and hand it in.

My design philosophy: **intent first, self-constructed criteria, convergence through reflection**. First sketch, from the Prompt's intent alone, a draft of "the properties a correct solution must satisfy"; then look at the candidates to infer "what a good solution looks like vs. a bad one" and turn that into a rubric; **triage** each predicate (route the ones that can be checked structurally to deterministic code, route the rest to agentic_judge); encode it into a grader; and finally enter the self-reflection loop to polish it.

> File layout: this `SKILL.md` is the main entry point; `meta-rules.md` contains the full text of the 27 general rules (01-27); `domain-strategy.md` covers domain-identification details; `domains/registry.json` + `domains/guides/` form the domain knowledge base (containing the full text of each domain's dedicated rules); `runtime/judge_harness.py` is the fixed library file that agentic_judge calls into. Read this file first, then load the sub-files as needed.

## Three Steps (Strict Order)

### Step 0 · Domain Identification (Before Step 1)

Match the task's keywords against `domains/registry.json`. On a hit, read `domains/guides/<domain_id>.md` and treat its `gate_policy` / `layer_hint` / `deterministic_predicates` / `agentic_judge_dimensions` / known pitfalls as priors for Steps 1-3 (where it conflicts with `meta-rules.md`, `meta-rules.md` wins). On no hit, triage from scratch using the Step 1.1 procedure, without applying any domain table. When a domain-specific hit occurs (e.g. `code/workspace-execution`), that domain guide's positive/negative example code is the **only** place this content lives — you must read the full guide; it is not a skippable "supplementary reference."

**What if multiple domains match at once?** A task's text can easily match more than one entry (e.g., text mentioning both "script" and "solve/optimize" will match both `code/workspace-execution` and `code/gt-recomputation`). Handle it as follows:

1. **Read all of them** — don't cherry-pick one. Each guide covers a different concrete predicate type, and they're usually not mutually exclusive (a single task can have both "must actually execute" and "numbers must be recomputed and cross-checked" predicates).
2. If multiple guides give conflicting `gate_policy`/`layer_hint` for the **same predicate**, resolve it using `meta-rules.md` Rule 15 (structural verifiability takes priority) — guides only provide prior reference, they never override the rules.
3. In the domain note inside `verifier_summary.md`, honestly list every `matched_domain` that hit (it can be a list) — don't report just one for the sake of looking tidy.

After Step 3 converges, append a domain note (`matched_domain` / `inferred_domain` / `key_pitfalls_hit` / `guide_useful`) to the end of `output/verifier_summary.md` — do not write any file into the `domains/` directory; additions/edits/removals in the domain knowledge base are the maintainer's responsibility.

### Step 1 · Decompose

Look only at `verifier_author_inputs/task_md.md` (just the `## Prompt` plus environment frontmatter; the grading standard has been physically isolated and is not visible). At this step, do **not** look at the candidates yet — sketch a draft of "properties that must be satisfied" independently from the Prompt's intent, so you avoid being steered by any particular candidate's specific approach (Rule 01).

Produce an `atomic_predicates` list, where each item looks like:

```
P1: A SKILL.md file exists at the workspace root
P2: SKILL.md's YAML frontmatter contains name and description fields
P3: diagnosis-report.md exists and describes both "access token" and "missing dependency" issue types
...
```

Every predicate **must be falsifiable by a counterexample** (Rule 05).

### Step 1.1 · Predicate Triage (Deterministic Code vs. agentic_judge)

For each Pi, ask in order:

```
Q1: Can it be verified via [file existence / field value / numeric range /
    independent recomputation & cross-check / actual execution]?
    Yes → track = deterministic
Q2: Is it essentially about [narrative quality / whether an argument holds /
    persuasiveness / completeness of explanation], and the workspace truly
    has no structurable anchor for it?
    Yes → track = agentic_judge (goes into nice-to-have, see Step 2)
Q3: Does it touch both (a checkable core plus a subjective shell)?
    Yes → split into two: Pi-a (deterministic anchor part) + Pi-b (agentic_judge
    quality part)
```

**Default to rejecting the agentic_judge route**, unless the answer to Q1 is clearly "no" and you can write down one concrete, specific reason. Produce a triage table and write it into `verifier_summary.md`:

```
P1 [deterministic] vip_report.json exists in the workspace and the VIP set matches the fixture record-by-record
P2 [deterministic] the VIP count and total revenue in the summary exactly match the fixture
P3 [split] whether the report's risk-attribution narrative for each VIP is sound and cites data
   → P3a [deterministic]: the report cites that VIP's revenue figure (existence anchor)
   → P3b [agentic_judge]: whether the attribution narrative's argument holds up, rather than being keyword padding
P4 [agentic_judge] whether the email's tone is appropriate and shows negotiated concessions
```

If the domain guide matched in Step 0 has `layer_hint=mostly-deterministic`, the vast majority of this task's predicates should land on the deterministic track — if you find yourself tagging a lot of them as agentic_judge, ask yourself whether you're taking a shortcut. If `layer_hint=mostly-agentic-judge`, use that guide's `agentic_judge_dimensions` as initial candidates, but still verify each one against Q1-Q3.

### Step 1.5 · Externalize Ambiguity Decisions

Write every "could be read loosely or strictly" interpretation in the spec into a table; for each one, give your initial choice plus a one-sentence rationale (Rule 03).

### Step 2 · Encode

Open `verifier_author_inputs/candidates/{harness}__{model}/` (each contains the `workspace/` end-state plus a `transcript.jsonl` trajectory). This serves two purposes: (1) understanding what the artifacts/environment look like; (2) comparing differences across candidates to infer grading dimensions and write them into `rubric.md`. Candidates are evidence only — they do not define the requirements (Rule 02); do not copy a candidate's specific function names or path literals verbatim.

Write `grader.py`, implementing it in two layers according to the Step 1.1 triage results:

```python
from judge_harness import invoke_agentic_judge

def grade(transcript: list, workspace_path: str) -> dict:
    # ---- Deterministic layer: structural/fixture checks, the sole source of the binary gate ----
    # Distinguish two kinds of keys: must-have (feeds the gate) vs. nice-to-have (feeds
    # only the score) — don't treat every deterministic signal as must-have; follow the
    # Step 1.1 triage table's annotations.
    deterministic_signals = {}
    deterministic_signals["p1_skill_md_exists"] = check_skill_md_exists(workspace_path)
    deterministic_signals["p2_frontmatter_valid"] = check_frontmatter(workspace_path)
    deterministic_signals["p3a_revenue_cited"] = check_revenue_cited(workspace_path)
    # ... (implement every predicate tagged [deterministic] in Step 1.1 here, following Rules 17/18/19)

    must_have_keys = ["p1_skill_md_exists", "p2_frontmatter_valid", "p3a_revenue_cited"]
    # The non-must-have part of the deterministic layer (if any) — even when must-have
    # fails, this part still counts toward score, so that multiple candidates that all
    # "fail the deterministic layer" on the same task don't all collapse to the same
    # score (score collapse gets penalized as a "tie" by the D3 ranking-discriminability
    # metric — see the score-spread self-check in Rule 16).
    nice_deterministic_keys: list[str] = []  # e.g. ["p4_optional_field_present"]
    deterministic_pass = all(deterministic_signals[k] >= 0.99 for k in must_have_keys)

    # ---- agentic_judge layer: only the subjective dimensions tagged [agentic_judge] in
    # Step 1.1; by default these feed only the score ----
    judge_schema = {"dimensions": {"narrative_coherence": {"description": "..."}}}  # from Pi-b in Step 1.1
    judge_prompt = "..."  # assemble the triage table's judge questions into judging instructions

    if deterministic_pass:
        judge = invoke_agentic_judge(judge_prompt, judge_schema, workspace_path=workspace_path)
    else:
        # The deterministic layer has already FAILed, so the gate outcome won't change —
        # but that doesn't mean you should skip judging and zero out this part of the
        # score. A task often has multiple candidates that "fail the deterministic layer,"
        # and they can still differ noticeably in narrative quality. D3 (ranking
        # discriminability) depends on exactly this kind of difference: if you treat them
        # all as 0, these candidates get scored as "tied" in D3's pairwise comparisons and
        # get penalized for it (Rule 16).
        # Compromise: still call agentic_judge once, but with k=1 (no multi-sample voting,
        # saving most of the budget), trading for a directional score usable for ranking
        # candidates against each other, rather than discarding this signal entirely.
        judge = invoke_agentic_judge(judge_prompt, judge_schema, workspace_path=workspace_path, k=1)

    nice_signals: dict[str, float] = {k: deterministic_signals[k] for k in nice_deterministic_keys}
    if judge["available"]:
        nice_signals.update({f"agentic_judge_{k}": v["score"] for k, v in judge["dimensions"].items()})
    nice_total = sum(nice_signals.values()) / max(1, len(nice_signals)) if nice_signals else 0.0

    outcome_passed = deterministic_pass   # the binary gate always looks only at the deterministic layer (the only exception is the "pure agentic_judge gate" below)

    signals = {**deterministic_signals, **nice_signals}
    criteria_list = [{"name": k, "must_have": k in must_have_keys} for k in signals]
    return {
        "outcome_passed": outcome_passed, "score": nice_total, "breakdown": signals,
        "criteria": criteria_list,
        # judge_meta is a structured field (not stuffed into the notes text) so the
        # evaluation side's ledger (Task D2) can read it directly without parsing free
        # text; tasks that don't use agentic_judge can omit this field.
        "judge_meta": judge,
        "notes": f"deterministic_pass={deterministic_pass} judge_available={judge['available']}",
    }
```

**The sole exception — the pure agentic_judge gate**: this is allowed only when, after Step 1.1 triage, you've confirmed the whole task has **no deterministic predicate at all** (purely creative/subjective; note that even an existence anchor like "does the deliverable exist" counts as deterministic, so this case is extremely rare):

```python
def grade(transcript, workspace_path):
    schema = {"dimensions": {
        "core_intent_satisfied": {"description": "Whether the deliverable satisfies the Prompt's core intent; must cite file paths and excerpts as evidence"},
    }}
    judge = invoke_agentic_judge(JUDGE_PROMPT, schema, workspace_path=workspace_path, k=5, min_agreement=0.8)
    if not judge["available"]:
        # Unavailable or samples disagree too much → conservatively rule FAIL, never PASS (Rule 25)
        return {"outcome_passed": False, "score": 0.0, "breakdown": {}, "criteria": [],
                "judge_meta": judge,
                "notes": "agentic_judge unavailable or samples disagree; fail-safe conservative FAIL"}
    core = judge["dimensions"]["core_intent_satisfied"]["score"]
    outcome_passed = core >= 0.99
    return {"outcome_passed": outcome_passed, "score": core,
            "breakdown": {"agentic_judge_core_intent_satisfied": core},
            "criteria": [{"name": "agentic_judge_core_intent_satisfied", "must_have": True}],
            "judge_meta": judge,
            "notes": f"pure-agentic_judge gate; agreement={judge['agreement']:.2f}"}
```

When you use this exception, you must state `gate=pure-agentic_judge` in the `## Gate Policy` section of `verifier_summary.md`, and list the concrete reasons "why no deterministic predicate could be found."

**The number of output files depends on whether agentic_judge is actually used**:
- If `grader.py` has no `[agentic_judge]`-track predicates at all, and no `import judge_harness`: the output is 3 files — `grader.py` / `rubric.md` / `verifier_summary.md`.
- If `grader.py` contains `from judge_harness import invoke_agentic_judge`: the output is 4 files — additionally **byte-for-byte copy** `judge_harness.py` from the skill's bundled template into `output/` (no modifications allowed, Rule 24).

When deciding which rules/domain guides apply, write every deterministic signal following Rule 17's fixture-first principle. When Step 0 identifies a matching domain, read that guide's full positive/negative examples (e.g., if `code/workspace-execution` is identified, you must read that guide in full — not just the one-line summary in `meta-rules.md` Rule 19).

### Step 3 · Self-Reflection (The Reflection Loop)

**This is an agent loop, not a one-shot checklist.** There is no bench, no evaluator, no gold telling me right from wrong — after writing a draft, I must repeatedly scrutinize and revise it in a loop until I'm confident or the budget runs out (recommended ≤3 rounds). Each round:

**(a) Actually run it / reason through it by hand**: if you can run it, actually run the grader against every candidate and look at the `outcome_passed` distribution; if you can't, work through each candidate mentally.

**(b) Reflect using unsupervised proxies (none of which rely on any reference answer):**

- **Over-leniency self-check (the most important one)**: if all K candidates PASS → be highly suspicious that the grader is too loose. Ask yourself: "what trick would let an obviously bad solution slip past my gate?" If it's too easy to pass → tighten it.
- **Discriminability self-check**: pick a PASS candidate and sabotage its key deliverable (delete a file, corrupt a critical field) — the grader should flip to FAIL. If it doesn't → that predicate is decorative, rewrite it.
- **Fixture ground-truth self-check (Rule 17)**: grep every function that contributes to a must-have; any full-score path that compares against the deliverable without first reading the expected value from the workspace input → must be rewritten; substring/ratio/loose-threshold hits alone are capped at 0.5.
- **Process-signal self-check (Rule 18)**: do any must-haves contain process predicates like "was some input consulted" or "does some call appear in the trajectory"? If so, demote them to nice-to-haves.
- **Executable-verification self-check (Rule 19)**: if the task requires an executable deliverable, check that the execution verification actually runs on the real `workspace_path`, not on a temp directory/fake scenario the grader built for itself.
- **agentic_judge keyword-proxy self-check (Rule 21)**: grep the function bodies of every predicate routed to agentic_judge; if any use keyword matching instead of an `invoke_agentic_judge(` call → must be rewritten.
- **agentic_judge grounding self-check (Rule 22)**: check, one dimension at a time, whether every dimension in `judge_prompt`/schema traces back to the Step 1.1 triage table — delete or rewrite any dimension that was invented out of thin air.
- **agentic_judge routing-leak self-check (Rule 27, the one most often overlooked)**: go through every predicate routed to agentic_judge and re-ask, one at a time, "can this predicate really not be checked structurally?"
- **agentic_judge mutation self-check (Rule 26)**: applies only when this task actually uses agentic_judge — pick a PASS candidate, artificially degrade the quality of its relevant dimension, and rerun; the corresponding score should drop noticeably.
- **agentic_judge copy-consistency self-check (Rule 24)**: applies only when the output includes `judge_harness.py` — confirm it is byte-for-byte identical to the skill's bundled template.
- **Score-spread self-check (Rule 16)**: if the score range between PASS and FAIL candidates is <0.15 → predicates are too shallow; go back to Step 1 and refine them.
- **Counterexample self-check**: for every atomic predicate, imagine a counterexample that gets it wrong, and confirm the grader catches it.
- **No-peeking self-check**: confirm you never opened the isolated directory holding the grading standard, at any point during authoring.
- **No-overfitting self-check**: confirm you didn't copy a specific candidate's function names/paths/literals verbatim, and didn't hardcode a candidate's identity.
- **stdlib-only self-check**: every `import` is from the standard library only (except `judge_harness`, which itself also only imports stdlib).

**(c) Fix it**: turn every weakness you found into an actual change, then go back to (a) for another round. **Convergence criteria**: over-leniency self-check passes + discriminability self-check passes + fixture ground-truth self-check passes (Rule 17) + process-signal self-check passes (Rule 18) + executable-verification self-check passes (if applicable, Rule 19) + agentic_judge keyword-proxy/grounding/routing-leak self-checks pass (if applicable, Rules 21/22/27) + agentic_judge mutation self-check passes (if applicable, Rule 26) + score-spread self-check passes (Rule 16) + reading through the rubric once more, your worry that "a solution that should FAIL would actually slip through" has been resolved.

Finally, reply with a short summary (≤200 characters):

```
Atomic predicates: 5 (deterministic 3 / agentic_judge 2)
Ambiguity decisions: 3
Reflection rounds: 2
Run/hand-check distribution: PASS=4 FAIL=4
Over-leniency: ✓  Discriminability: ✓  Fixture truth: ✓  Process signals: ✓  Executable verification: n/a
agentic_judge keyword-proxy: ✓  Grounding: ✓  Routing leak: ✓  Mutation: ✓
Score spread: ✓  No peeking: ✓  No overfitting: ✓  stdlib only: ✓
Output: 4 files (includes judge_harness.py)
```

## Anti-Leakage + Generalization Guardrails

**Anti-leakage (during authoring)**: never open the isolated directory holding the grading standard, at any point. Your criteria may only come from the task-layer inputs. Whether you peeked at the answer is determined by scanning the execution trajectory — peeking invalidates the run.

**Generalization (grader quality)**: never hardcode a candidate's identity to grade it; never grade by byte-equality or hash-equality; never copy a specific candidate's function names or path literals verbatim (unless the task explicitly requires it). At runtime, the grader only ever receives `(transcript, workspace_path)` — it physically cannot read the answer (Rule 14).

## Internal Invariants

- The number of output files depends on whether agentic_judge is used (see Step 2): 3 files if not used (grader.py / rubric.md / verifier_summary.md), 4 if used (plus judge_harness.py)
- Beyond the 5 standard fields (outcome_passed/score/breakdown/criteria/notes), if agentic_judge was called, `grade()`'s return value must carry an extra optional field `judge_meta`, holding `invoke_agentic_judge()`'s return dict verbatim — for the evaluation side to read as structured data; do not fold this information into the free-text `notes`
- Make no direct network requests (HTTP/socket) whatsoever; the only permitted external interaction is a local agent-CLI subprocess call made via `judge_harness.invoke_agentic_judge()`
- `judge_harness.py` (if produced) is a byte-for-byte copy of the skill's bundled template; modification is not allowed
- Do not modify `verifier_author_inputs/`
- Do not open candidates/ before Step 1 is complete
- `grader.py` only imports stdlib (except `from judge_harness import invoke_agentic_judge`); `judge_harness.py` itself also only imports stdlib
- Reply with ≤200 characters when done
