# Rubric: Contract Legal Analysis (SSA-2024-09172)

## Task Intent

Read `sample_contract.pdf`, perform thorough legal analysis, save to `contract_analysis.md` with four sections: Key Dates and Deadlines (chronological), Party Obligations (by party), Risks and Concerns (per party, covering liability/termination/IP/data protection), Financial Summary.

## Criteria (maps 1:1 to `grader.py` breakdown keys)

### Must-Have (Deterministic Gate)

| Key | Weight | Description |
|-----|--------|-------------|
| `p1_deliverable_exists` | Gate | `contract_analysis.md` exists (root or `output/`) with ≥400 characters |
| `p2_required_sections` | Gate | All four required sections present with substantive body (≥80 chars after heading) |
| `p3_parties_from_fixture` | Gate | Both party names derived from PDF appear in analysis |
| `p4_total_value_from_fixture` | Gate | Total contract value $2,400,000 from PDF cited correctly |
| `p5_payment_amounts_from_fixture` | Gate | All distinct milestone payment amounts from PDF present ($360k×2, $600k, $480k, $240k) |
| `p6_obligations_by_party` | Gate | Party Obligations section has Provider and Client subsections each with ≥3 contract-derived obligation signals |
| `p7_milestone_dates_from_fixture` | Gate | ≥5 of 6 payment due dates from PDF appear in dates section |
| `p8_contract_number_from_fixture` | Gate | Contract number SSA-2024-09172 from PDF cited |
| `p9_risks_both_parties` | Gate | Risks section substantively addresses both Provider and Client perspectives |

### Nice-to-Have (Score Only)

| Key | Description |
|-----|-------------|
| `p10_effective_date_from_fixture` | Effective date September 15, 2024 cited |
| `p11_financial_conditions_from_fixture` | Retainage 10%, late interest 1.5%, net-30 payment terms cited in financial section |
| `p12_risk_topics_from_fixture` | ≥5 Prompt risk categories (liability, termination, IP, data protection, etc.) with section references |
| `agentic_judge_risk_analysis_substance` | Per-party risk analysis with reasoning and contract clause references (not keyword stuffing) |
| `agentic_judge_legal_reasoning_depth` | Analysis explains practical legal/business implications beyond extraction |

## Scoring

- **PASS**: All must-have keys ≥ 0.99
- **Score**: Mean of nice-to-have deterministic + agentic_judge dimensions (0 if judge unavailable)

## Anti-Patterns (FAIL)

- Missing deliverable or empty file
- Sections present but without substantive content
- Financial figures not matching contract PDF
- Obligations not organized by party
- Risks listing keywords without per-party analysis
- Fabricated parties or amounts not in source contract
