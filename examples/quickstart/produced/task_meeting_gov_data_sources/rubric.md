# Rubric: NASA UAP Meeting Data Sources Extraction

## Task Intent

The agent must read `transcript.md` and produce `data_sources.md` cataloguing every data source, sensor, database, or measurement system discussed during NASA's first public UAP meeting. Each source needs structured metadata, six required category groupings, and a summary table at the top.

## Scoring Model

- **Gate**: all must-have criteria (`p1`–`p6`) must score ≥ 0.99.
- **Continuous score**: `p7_minimum_source_count` (nice-to-have) averages into `score` when the gate passes.

---

## Criteria (aligned 1:1 with `grader.py` breakdown keys)

### p1_deliverable_exists (must-have)

`data_sources.md` exists in the workspace root or `output/` subdirectory and contains more than 200 characters of substantive text.

| Score | Condition |
|-------|-----------|
| 1.0 | Deliverable present and non-trivial |
| 0.0 | Missing or only a stub |

### p2_summary_table (must-have)

A markdown summary table appears near the top of the deliverable with columns for **category** and **owner/operator**, plus at least two data rows.

| Score | Condition |
|-------|-----------|
| 1.0 | Table with category + owner columns and ≥2 data rows |
| 0.5 | Table present but missing a required column |
| 0.0 | No qualifying table |

### p3_categories_complete (must-have)

All six Prompt-required category groups are represented in the document:

1. Government/Military Sensors
2. Civilian Aviation Systems
3. Space-Based Assets
4. Ground-Based Scientific Instruments
5. Crowdsource/Public Data
6. Databases/Archives

| Score | Condition |
|-------|-----------|
| 1.0 | All 6 groups found |
| 0.5 | 4–5 groups found |
| 0.0 | ≤3 groups found |

### p4_per_source_fields (must-have)

Detailed entries include the six required fields per source: Name/Type (via headings), Owner/Operator, Description, Relevance to UAP, Limitations, and Who referenced it. Verified structurally by counting field-label occurrences relative to source-entry count.

| Score | Condition |
|-------|-----------|
| 1.0 | ≥12 sources and all five field labels appear ≥8 times each |
| 0.5 | Partial field coverage or 8–11 sources |
| 0.0 | <5 sources or almost no field labels |

### p5_transcript_coverage (must-have)

Expected data-source anchors are **derived at runtime** from `transcript.md` (sensor names, portals, systems explicitly mentioned). The deliverable must cover ≥85% of those anchors using contextual match terms.

| Score | Condition |
|-------|-----------|
| 1.0 | ≥85% anchor coverage |
| 0.5 | 65–84% coverage |
| 0.0 | <65% coverage |

### p6_content_not_degenerate (must-have)

The deliverable is not garbage output: sufficient lexical diversity, no runaway phrase repetition, and enough detail sections beyond a lone summary-table row.

| Score | Condition |
|-------|-----------|
| 1.0 | Healthy diversity and substantive detail |
| 0.0 | Repetitive/degenerate or detail-free stub |

### p7_minimum_source_count (nice-to-have)

Comprehensiveness signal based on distinct source entries (summary-table rows or numbered section headings).

| Score | Condition |
|-------|-----------|
| 1.0 | ≥15 distinct sources |
| 0.5 | 8–14 sources |
| 0.0 | <8 sources |

---

## Cross-Predicate Invariants

- If `p1` fails, structural/content signals are capped at 0.5.
- If `p6` fails (degenerate content), `p5` coverage is capped at 0.5.
