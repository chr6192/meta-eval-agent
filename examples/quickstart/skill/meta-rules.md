> Language: **English** · [中文](meta-rules.zh-CN.md)

# verifier-author Grading Rules — Full Text (01-27)

> This file is referenced by SKILL.md as needed. Rules are numbered with two digits; the numbering itself carries no semantic order and is only a stable reference anchor — each rule's name already tells you what it governs, so no lookup table is needed.

## 01. Intent Before Evidence (intent-before-evidence)

First sketch a draft of "properties that must be satisfied" from the Prompt alone — **opening the candidates before finishing this draft is strictly forbidden**. Rationale: the grading standard is hidden, and the candidates are the only visible glimpse of "how others did it"; if you look at them first and reverse-engineer a standard from them, you'll mistake "what most candidates did" for "what the spec requires" (overfitting — see Rule 02). Correct order: draft the Prompt's intent → look at the candidates to infer "the dimensions that separate good from bad" → write the rubric → encode it. Candidates supply **evidence**; the Prompt supplies the **requirements**.

## 02. Consensus Is Not the Spec (consensus-not-spec)

All K candidates doing the same thing **does not mean** that thing is required by the spec — they may all be making the same mistake. Grade against the spec, not against "what most candidates did."

## 03. Make Ambiguity Explicit (explicit-ambiguity-log)

Any interpretation that "could be read loosely or strictly" must be written as an `Amb-N` entry, with an initial choice plus a one-sentence rationale — never silently hard-code one reading.

## 04. Be Suspicious of All-Pass (all-pass-suspicion)

If working through it by hand shows all K candidates PASS, stop and ask yourself: did an ambiguity decision pick the lenient reading by mistake? At minimum, re-run every `Amb-N` entry against its strict version.

## 05. Predicates Must Be Falsifiable (falsifiable-predicate)

As soon as you finish writing an atomic predicate Pi, ask yourself: imagine a candidate that **gets this wrong** or **doesn't do it** — can the check catch it? If you can't think of a counterexample → the predicate is too abstract; refine or split it. Counterexamples must target the **deliverable's content**, not its **file shell / substring shell** — "the file exists but its content is empty/wrong" also counts as a counterexample; mere path existence or a single anchor hit must not be the sole path to full score (this compounds with Rule 09). After writing each signal, leave a one-line counterexample annotation in the docstring/comment.

## 06. Every must-have Feeds the Gate (must-have-gate-is-absolute)

Every signal tagged as must-have feeds the gate — **all of them**, no picking a subset. If a particular one shouldn't be allowed to block the whole thing, demote it to a nice-to-have and write your reasoning into `verifier_summary.md`.

## 07. Three-Tier Scores Need Concrete Examples (three-tier-docstring)

When implementing each signal, explicitly list in the docstring/comment what concrete situation corresponds to each of the 0 / 0.5 / 1.0 tiers — a vague description like "give 0.5 for partial compliance" is not acceptable.

## 08. Signal Names Must Be Semantic (semantic-signal-naming)

There's no need to align with any hidden official field names, but your own `signals`/`breakdown` keys must be semantic (describing "what's being checked," e.g. `report_file_valid`), and must map one-to-one with the criteria listed in `rubric.md`, so downstream consumers can align them easily.

## 09. No Passing the Gate on Keywords Alone (no-keyword-only-pass)

When a signal has multiple decision branches internally: at least one non-fallback branch must be a structural check (reading a JSON/YAML field, parsing a markdown section, reading a trajectory tool name). Keyword matches / mere-existence checks / single-substring regex hits are capped at 0.5 and cannot, on their own, clear a must-have's gate. Mark in the docstring/comment which part is the structural check and which part is the keyword hit.

## 10. Coverage Scores Need an Anchor (coverage-needs-anchor)

A "PASS if k/N items are hit" style signal cannot feed a must-have gate on its own — it must be paired with a same-name, same-tier anchor signal. A coverage judgment of ≥0.99 must also satisfy "at least half of the hits carry an anchor."

## 11. Cross-Predicate Invariants (cross-predicate-invariants)

Explicitly list the mutual-exclusion/co-occurrence/dependency relationships between predicates, and check them one by one with a consistency-check function at the end of `grade()`; any violation forces the involved must-haves to 0.

## 12. Full-Score Threshold and Alias Cap (full-match-alias-cap)

The full-score threshold for coverage-type must-haves is hard-set at 100% hit rate (relax this only when the sample size is very small, and you must document why); alias/synonym OR sets are capped at 2 entries — beyond that, switch to a structural check instead.

## 13. Hard-Gate Naming and Short-Circuit Returns (hard-gate-early-return)

Any must-have whose name implies "must not / forbidden / safety / hard requirement" is treated as a hard gate without exception: hitting the violation branch returns 0 immediately — do not write OR-based bailout logic like "it only counts as a violation if there's no remedy."

## 14. Runtime Contract (runtime-contract)

The grader may only read: files listed in the task's input manifest, artifacts the agent wrote to disk, and the `transcript` parameter passed in. At runtime it receives `(transcript, workspace_path)`; referencing any directory name that only exists during the preparation phase is **strictly forbidden**. Each signal must note its data source in the docstring/comment (deliverable / workspace input file / raw trajectory); add a section to `verifier_summary.md` listing every data-source path, and perform a self-check confirming each source can be verified to exist at least once.

## 15. Structurally-Verifiable must-haves May Not Use an Averaged Gate (deterministic-gate-no-lenient-mean)

Before coding the gate formula, ask of each must-have: can it be judged structurally via file existence / field value / numeric range / trajectory tool name? As soon as ≥1 answers "yes," the gate must be "all must-haves ≥0.99 AND the nice-to-have average meets its bar" — never dilute this with a lenient formula like "must-have average ≥ some threshold." Only when **every single** must-have is a subjective dimension with no structural anchor is the "pure agentic_judge gate" described in SKILL.md permitted (see Rules 20/23). The `## Gate Policy` section of `verifier_summary.md` must state exactly which gate type was used and the basis for that decision.

## 16. Score-Spread Self-Check (score-spread-selfcheck)

After running self-reflection, compute the score range between PASS candidates and FAIL candidates: range < 0.15 → predicates are too shallow and lack discriminability; you may not claim convergence — go back and add anchors / add fixture cross-checks / tighten the gate. Range ≥ 0.25 with a non-all-PASS distribution → this check passes.

## 17. Fixture Ground Truth First (fixture-truth-first)

This is the single most important rule for preventing "shallow checks that are too lenient," and it applies to every must-have that requires a structural cross-check:

1. The full-score path must **first** read a checkable ground truth from the workspace's **input files**, and only **then** cross-check it, field by field or value by value, against the candidate's **deliverable** — this order cannot be reversed, and you cannot fabricate a lookup table inside the grader itself (one that is neither read from the workspace input nor the candidate's deliverable).
2. Any path that relies solely on keyword occurrence counts, section-title hits, coverage-ratio thresholds, or loose numeric comparisons (e.g. "similarity ≥0.85 counts as passing") → that signal is capped at 0.5 and **must not**, on its own, be sufficient for a must-have to pass.
3. OR-based bailout logic ("full score if either A or B hits") is forbidden; full score must be achieved by multiple independent conditions being satisfied simultaneously (AND).
4. If a must-have requires genuine execution verification against the candidate (see Rule 19), the expected result must likewise be derived from the workspace input — not a sample set hardcoded in the grader, nor a fake scenario cooked up on the spot in a temp directory.
5. Note in the docstring/comment which workspace input file this full-score path depends on, and which field of the deliverable it's being cross-checked against.

**Positive example**:

```python
def grade(transcript, workspace_path):
    expected = _derive_expected_from_workspace(workspace_path)   # Step 1: read ground truth from the input first
    signals = {}
    signals["classification_correct"] = _score_against_expected(
        _read_deliverable_text(workspace_path), expected,        # Step 2: cross-check against the deliverable field by field
    )
    ...

def _score_against_expected(deliverable_text, expected):
    """
    1.0 - every expected record has a correct match in the deliverable
    0.5 - at least half of the records are correct (must not feed a must-have gate alone)
    0.0 - fewer than half
    """
    hits = sum(1 for rec in expected["records"] if _record_matches(deliverable_text, rec))
    ratio = hits / max(1, len(expected["records"]))
    if ratio >= 1.0:
        return 1.0
    if ratio >= 0.5:
        return 0.5
    return 0.0
```

**Negative example**:

```python
def _check_something(deliverable_text, hardcoded_keywords):
    # Problem: hardcoded_keywords isn't read from the workspace input — it's made up inside the grader
    # Problem: substring hits stand in for exact field-level cross-checks
    return 1.0 if any(kw in deliverable_text for kw in hardcoded_keywords) else 0.0
```

**Self-check action**: run a "content sabotage" test on a PASS candidate — corrupt a core field and rerun; that signal must drop below 0.99. Otherwise the signal isn't actually checking content, it's decorative, and must be rewritten.

## 18. Process Signals May Not Be must-haves (process-predicates-nice-only)

**Process** signals such as "was some input file consulted/read in the trajectory" or "is the tool-call sequence complete" may only be nice-to-haves — you may never rule FAIL solely because "the trajectory doesn't show some action." If the Prompt explicitly requires that some input be referenced, check instead whether the **deliverable's content** reflects that input's key information (Rule 17); you cannot substitute "a certain call appears in the trajectory" for that.

## 19. Executable Deliverables Need Real Execution Verification (executable-needs-real-run)

When the Prompt requires producing a runnable script/command/workflow: at least one must-have must be an **execution-type** signal — actually run the deliverable on the candidate's `workspace_path` and probe its behavior (exit code, output, side effects); relying on "the file exists" or "some substring appears in the command text" is not enough. Execution verification **must** happen on the real `workspace_path` that's passed in; building a temp directory and a fake scenario inside the grader and running against that is **forbidden** (a candidate's command succeeding in a fake scenario does not mean it's correct in the candidate's real workspace). Expected results must likewise be derived from the workspace input (Rule 17). When a "Code"-related domain is matched, refer to that domain guide's specific code examples.

## 20. Subjective Dimensions Must Go Through agentic_judge (subjective-needs-agentic_judge)

There's no visibility into any hidden official grading rubric, but for many tasks, "right vs. wrong" lives precisely in subjective narrative dimensions (whether an argument holds up, whether an explanation is complete, whether the tone is appropriate). These dimensions **may not** be approximated by "find a few keywords/phrases and turn them into a regex" — you must call `judge_harness.invoke_agentic_judge()` so the agent actually reads the evidence and renders a verdict with citations. Which predicates truly "cannot be checked structurally" must be decided one at a time using SKILL.md's predicate-triage procedure; default to rejecting this branch, and allow it only once you've confirmed there really is no structural anchor.

## 21. Never Use Keywords to Impersonate agentic_judge (no-keyword-proxy-for-judge)

Any predicate triaged as "routed to agentic_judge" **must** be implemented as an `invoke_agentic_judge(...)` call — approximating it with a keyword list or regex is forbidden. This is worse than an honest structural check, because it has low precision while pretending "a judgment was made." During self-reflection you must grep every function body in `grader.py` that corresponds to an agentic_judge-routed predicate; if any use keyword matching instead of an `invoke_agentic_judge` call, they must be rewritten.

## 22. Judge Questions Must Be Grounded in a Concrete Predicate (judge-prompt-grounded)

Every dimension in `judge_prompt` and its schema must map one-to-one to a specific "routed to agentic_judge" predicate description from the triage stage. Inventing an anchor-less dimension like "how's the overall quality" on the fly during encoding is forbidden — every dimension must be a concrete judgment for which a counterexample could be given.

## 23. Judge Results Feed Only the Score by Default (judge-default-score-only)

By default, the result of `invoke_agentic_judge` contributes only to the nice-to-have/continuous score. Only when the entire task is confirmed to have **absolutely no** structurally-verifiable must-have may you wire it into the final PASS/FAIL decision via the "pure agentic_judge gate" described in SKILL.md (k≥5 sampling, agreement ≥0.8, rule FAIL when unavailable). For any mixed task that is "partly structurally verifiable, partly subjective," PASS/FAIL always looks only at the structurally-verifiable part.

## 24. Copy the Judge Harness, Never Rewrite It (judge-harness-copy-only)

`judge_harness.py` (if a task uses it) must be a byte-for-byte copy of the skill's bundled template file. During self-reflection, confirm this with `diff`; if you find yourself wanting to "improve" the sandboxing/voting logic — don't. That's the maintainer's responsibility, and breaking it risks introducing a sandbox-escape vulnerability.

## 25. Judge Unavailability Defaults to a Conservative Ruling (judge-fail-safe-on-unavailable)

When `invoke_agentic_judge` returns unavailable (the agent CLI doesn't exist / timed out / the k samples disagreed too much): if that dimension only affects score, record 0, and place `invoke_agentic_judge`'s raw return value in its entirety into the `judge_meta` field of `grade()`'s return value (a structured field, not folded into the free-text `notes` — the latter is easy for downstream tools to fail to parse); never silently treat it as full score or simply ignore it. If that dimension is the "pure agentic_judge gate," the final verdict must be FAIL, never PASS.

## 26. Judge Dimensions Need a Mutation Self-Check (judge-mutation-selfcheck)

Pick a PASS candidate and deliberately, noticeably degrade the quality of its relevant dimension (delete key argument paragraphs, replace them with empty boilerplate), then regrade; the corresponding agentic_judge dimension's score must drop noticeably. If it doesn't → `judge_prompt` isn't actually grounded in concrete evidence requirements — go back to Rule 22 and rewrite it.

## 27. Judge Triage Needs a Routing-Leak Self-Check (judge-routing-leak-selfcheck)

Go through every predicate routed to agentic_judge, one at a time, and re-ask "can this really not be checked structurally?" — be especially wary when a predicate's description contains a specific field name/number/filename (these can usually be checked structurally), or when the matched domain guide is clearly `mostly-deterministic` yet you've still tagged several predicates as agentic_judge. If you catch a lazy routing decision, move it back to a structural check and rewrite it.
