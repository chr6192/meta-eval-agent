---
id: task_contract_analysis
name: Contract/Legal Analysis
category: Legal
subcategory: Contract
timeout_seconds: 600
input_modality: text-only
external_dependency: none
workspace_files:
- source: assets/T055_pinchbench_contract_analysis/sample_contract.pdf
  dest: sample_contract.pdf
labels:
  scenario: Legal/Contract
  capabilities:
  - Logic_Reasoning
  - Tool_Use
  - Planning
  modality:
    type: text
  complexity: L3
  environment: closed
---

## Prompt

Read the file `sample_contract.pdf` in my workspace. It is a Software Services Agreement between two companies. Perform a thorough legal analysis and save your findings to `contract_analysis.md`.

Your analysis must include the following sections:

1. **Key Dates and Deadlines** — Extract all significant dates, milestones, and deadlines mentioned in the contract, presented in chronological order.
2. **Party Obligations** — Summarize the key obligations of each party (Provider and Client), organized by party.
3. **Risks and Concerns** — Identify potential risks, unfavorable clauses, or areas of concern for each party. Consider liability limitations, termination conditions, IP ownership, data protection requirements, and any other provisions that could be problematic.
4. **Financial Summary** — Summarize the total contract value, payment schedule, and any financial conditions (late fees, retainage, etc.).


## Additional Notes

This task tests the agent's ability to:

- Parse a multi-page PDF document containing a legal contract
- Extract structured information (dates, obligations, financial terms) from dense legal text
- Perform analytical reasoning about legal risks and implications, going beyond mere summarization
- Organize findings into a clear, professional analysis document
- Identify nuances such as geographic arbitration disadvantages, liability carve-outs, and IP retention clauses

The mock contract is a realistic Software Services Agreement containing typical enterprise software development terms. The agent must demonstrate both comprehension of the document and the ability to reason about what the terms mean in practice for each party.
