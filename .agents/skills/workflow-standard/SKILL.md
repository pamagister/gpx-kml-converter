---
name: workflow-standard
description: Execute a bounded task or one standalone feature. For any request to execute a plan or named plan phase, use workflow-autopilot instead, even when only one phase is selected.
---

# Standard Workflow

Use this skill for a bounded task or one standalone feature. Follow the workflow routing rules in the always-loaded `AGENTS.md`.

Do not use this workflow for requests to implement, execute or continue a plan or any named phase/work package from a plan. Such requests use `workflow-autopilot`, even if the user selects only one phase.

## Select the mode

- **Task mode (A):** review, typo fix, documentation adjustment, small refactor or similarly bounded change.
- **Feature mode (B):** implement one feature or a self-contained bug fix that is not framed as execution of a plan.
- If the requested scope clearly describes a standalone feature implementation, use Feature mode. Otherwise use Task mode.

## Shared task loop

1. Inspect repository status, relevant instructions, implementation, tests and configuration. Preserve pre-existing user changes.
2. Understand the acceptance criteria. Ask only if a consequential ambiguity cannot be resolved safely.
3. Implement the smallest complete change.
4. Review the diff before testing. Check scope, correctness, unintended changes and consistency with existing conventions.
5. Run relevant tests and non-mutating checks. Use the project's actual configured commands; do not assume a generic `make check` target exists.
6. Fix failures caused by the task and repeat the affected checks. Do not hide or weaken failing tests.
7. Review the final diff again and report exactly which checks were run.

## Task mode (A)

- Stage only files or hunks that belong to this task.
- Leave pre-existing user changes unstaged. If a file already contained unrelated changes and safe partial staging is not practical, leave it unstaged and explain why.
- Do not commit or push.
- Suggest a concise Conventional Commit message inline in the final chat response when a commit would be appropriate.
- Do not create GitHub issues automatically for ordinary Task mode.

## Feature mode (B)

1. Load `git-workflow` before GitHub or Git operations.
2. Search for an accurate matching open GitHub issue before implementation.
3. Reuse a suitable open issue. Do not edit its title, body, labels, assignees or state; comments may be added when useful.
4. If no suitable open issue exists, create one without asking the user. Keep its scope aligned with the requested feature.
5. Implement and verify the feature using the shared task loop.
6. Stage only task-related changes and create a coherent Conventional Commit referencing the issue.
7. Do not push.
8. Do not close a reused or newly created issue in this mode; report the issue and commit references.

## Safety and completion

- Never use indiscriminate staging such as `git add .` or `git add -A`.
- Never discard, overwrite or commit unrelated user changes.
- Never commit known failing or unverified changes.
- If required credentials or permissions are unavailable, continue with work that does not depend on them and report the limitation.
- If a blocker makes correct completion impossible, stop at that boundary and explain what is needed.
