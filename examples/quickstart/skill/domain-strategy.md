> Language: **English** · [中文](domain-strategy.zh-CN.md)

# Step 0 · Domain Identification and Routing (verifier-author sub-file)

> Executed **before** Step 1 (decomposing the task). This file is referenced by SKILL.md.

---

## Design Intent

The purpose of the domain system is to **accumulate, across repeated experiment iterations, effective verifier-construction references for each domain**, for verifier-author to reuse — reducing the cost of exploring from scratch every time.

- `domains/registry.json`: an index of all known domains (id, keywords, gate_policy, guide path)
- `domains/guides/{domain_id}.md`: the verifier-construction reference guide for each domain (including typical predicates, how to apply EX, known pitfalls)

**The operator (skill-optimizer) owns CRUD**: after each audit round, the optimizer adds/removes/edits registry entries and guide files based on patterns the auditor found (see §4 of this file). verifier-author is a **read-only consumer** and never writes discovered records.

---

## Step 0-1 · Keyword Matching

Read the current task's `verifier_author_inputs/task_md.md` (frontmatter + the `## Prompt` section).

Cross-reference `skill/domains/registry.json`: compare against the `keywords` field of each entry; if any keyword appears in the task text (case-insensitive), count it as a hit.

Output:
- On a hit: `matched_domain = [<domain_id>, ...]` (can be a list), `guide_paths = [<domains/guides/...>, ...]`
- On no hit: `matched_domain = []`

> **When multiple domains match at once, read all of them — don't cherry-pick one.** Each guide covers a different concrete predicate type, and they're usually not mutually exclusive. If multiple guides give conflicting `gate_policy`/`layer_hint` for the same predicate, resolve it using `meta-rules.md` Rule 15.

---

## Step 0-2 · On a Hit → Read the Domain Guide

```bash
# On a hit, read **all** matched guides inside the sandbox (don't read just one):
cat skill/domains/guides/<domain_id>.md   # repeat for every domain_id in matched_domain
```

Carry the guide's content into Steps 1–3:

| Guide field | Purpose |
|---|---|
| `gate_policy` | Prior for the gate formula chosen in Step 2 (still bound by Rule 15's structural-verifiability priority) |
| `layer_hint` | Prior reference for the Step 1.1 predicate triage (`mostly-deterministic`/`mixed`/`mostly-agentic-judge`) — not a forced conclusion; each predicate must still be verified against Q1-Q3 |
| `deterministic_predicates` | Recommended check dimensions for drawing atomic_predicates in Step 1 |
| `agentic_judge_dimensions` | Starting-point reference for drafting `judge_prompt`/schema when a predicate is tagged agentic_judge in Step 1.1 |
| Known pitfalls | Key self-check items for Step 3 self-reflection |
| Positive/negative example code | Pattern reference for encoding in Step 2 — the **full text** of domain-specific rules (e.g. Code's execution verification, Security's record-by-record cross-check) lives **only in the corresponding guide**, is not duplicated in `meta-rules.md`, and must be read in full when that domain is matched |

> A domain guide is a **prior hint** — it does not replace the self-reflection in Steps 1–3; where it conflicts with `meta-rules.md`, `meta-rules.md` wins.

---

## Step 0-3 · No Hit → Triage per Step 1.1

When no domain matches, don't apply any domain table — triage from scratch using `SKILL.md`'s Step 1.1 predicate-triage procedure (Q1–Q3), and proceed into Step 1 as usual.

---

## Step 0-4 · Emit a Domain Note After Step 3 Ends

After Step 3's self-reflection converges, append a brief domain note to the end of `output/verifier_summary.md` (**do not write a file into domains/ — only append to the summary**):

```markdown
## Domain Note
- matched_domain: [<domain_id>, ...] (can be a list; write `[]` if no hit; if multiple hit, list all of them honestly — don't report just one)
- inferred_domain: <if no hit, the inferred domain hierarchy name, e.g. office/financial-report; write null if a domain was matched>
- key_pitfalls_hit: [<concrete counterexample patterns found during the Step 3 self-check that match the domain guide's `known_pitfalls`, for the optimizer's reference>]
- guide_useful: <yes/no/n-a> (fill in on a hit: whether the guide's known pitfalls were actually encountered)
```

These notes are collected by **verifier-auditor**, and **skill-optimizer** decides whether to add/revise domain entries based on them (see §4).

---

## §4 · The Optimizer's CRUD Responsibilities (Each Iteration Round)

> This section is for skill-optimizer's reference; verifier-author does not need to act on it.

### Adding a Domain (CREATE)

When the auditor finds that inferred_domain recurs across a class of tasks (≥3 tasks all infer the same domain name), and there's already a clear, reusable verifier-construction pattern, the optimizer does the following:

1. Append an entry to `domains/registry.json`:

```json
{
  "domain_id": "<hierarchical name, e.g. office/financial-report>",
  "category": "<Code|Office|Safety|Multimodal|Creative|...>",
  "description": "...",
  "keywords": ["...", "..."],
  "gate_policy": "strict|strict-if-checkable",
  "layer_hint": "mostly-deterministic|mixed|mostly-agentic-judge",
  "deterministic_predicates": ["..."],
  "agentic_judge_dimensions": [
    {"dimension": "...", "judge_question": "..."}
  ],
  "anchor_hints": ["..."],
  "known_pitfalls": ["..."],
  "verifier_guide": "guides/<domain_id>.md",
  "discovered_in": "<experiment id>",
  "last_updated": "<experiment_iter_N>",
  "deprecated": false
}
```

> In `registry.json` today, `gate_policy` only ever takes the values `strict` (structural-verifiability priority) and `strict-if-checkable` (includes agentic_judge dimensions, tightened according to how verifiable it is) — there is no `lenient` value. An empty `agentic_judge_dimensions` array is usually paired with `layer_hint: mostly-deterministic`.

2. Create `domains/guides/<domain_id>.md` (following the format of existing guides).

### Updating a Domain (UPDATE)

When an existing domain's guide proves not precise enough (tasks in the same domain still show a high rate of false-pass / false-fail), the optimizer revises it:
- Update that entry's `known_pitfalls`, `anchor_hints`, `gate_policy` in `registry.json`
- Revise the corresponding section of the guide file, noting the version (e.g. `v2 · revised 260630_composer25_iter_3`)
- Update the `last_updated` field

### Freezing/Deprecating a Domain (SOFT DELETE)

When a domain's guide goes 3 consecutive rounds without a hit and without contributing any improvement, it may be set to `"deprecated": true` (not physically deleted); when verifier-author matches a deprecated domain, it skips loading the guide.

### Reinforcing an Existing Domain

When the auditor finds that the guide is missing some pitfall, the optimizer appends an entry to the guide's §4 "Known Pitfalls," and notes it in §5 "Iteration Log."

---

## File Layout

```
skills/verifier-author/domains/
├── registry.json            # domain index (optimizer CRUD)
└── guides/                  # per-domain verifier-construction reference (optimizer CRUD)
    ├── automation-platform/
    │   └── agent-config.md
    ├── office/
    │   └── financial-report.md   # (created by the optimizer once a pattern is found)
    └── ...
```
