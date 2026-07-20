---
id: task_gh_issue_triage
name: GitHub Issue Triage
category: Software Engineering
subcategory: GitHub
timeout_seconds: 300
input_modality: text-only
external_dependency: fws
workspace_files: []
labels:
  scenario: Software_Engineering/GitHub
  capabilities:
  - Tool_Use
  - Planning
  - Logic_Reasoning
  modality:
    type: text
  complexity: L3
  environment: open
---

## Prompt

You have access to a GitHub repository through the `gh` CLI tool (`gh --help` for usage). The repository is `testuser/my-project`.

Review the open issues and pull requests:

1. List all open issues and PRs
2. Read each one to understand its content
3. For the most critical issue, add a comment with your analysis and suggested next steps
4. Create a triage report saved to `triage_report.md` with priority, category, and recommended action for each item, sorted by priority


## Additional Notes

This task requires [fws](https://github.com/juppytt/fws) to be running as a mock server. The test runner should execute `fws server start` before the task begins and set environment variables via `eval $(fws server env)`.

Seed data includes: 1 repo (testuser/my-project), 2 open issues (#1 "Fix login bug" with a comment, #2 "Add dark mode support"), and 1 open PR (#3 "Fix SSO login flow").
