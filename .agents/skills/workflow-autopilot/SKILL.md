---
name: workflow-autopilot
description: Execute a complete plan or selected plan phase autonomously, including issue-first tracking, plan updates, commits, batched pushes and CI gates. Use even for a single selected phase.
---

# Autopilot Workflow

Use this workflow whenever the user asks to implement, execute or continue a plan, or selects one or more phases/work packages from a plan. This applies even when only one phase is selected. The user does not need to say "Autopilot" or know this internal mode name.

Execute only the phase(s) or work packages selected by the user. Do not proceed into later phases without authorization. Load `git-workflow` before GitHub or Git operations.

## Input plan

The plan may be:
- Markdown pasted directly into the prompt, or
- Any user-specified Markdown file path (for example, `plan.md`).

Do not require a fixed filename or a separate `tasklist.md`. The plan is the single source of truth for scope, decisions, work packages, acceptance criteria and progress.

A useful plan normally contains an objective, constraints/decisions, phases, coherent work packages and verifiable acceptance criteria. If it is too vague to execute safely, clarify only the blocking decisions before starting.

## Preparation

1. Inspect repository status, current branch, relevant instructions and the supplied plan. Preserve all pre-existing user changes.
2. Identify the exact selected phase(s), their dependencies, work packages and acceptance criteria. Do not silently expand scope.
3. Reconcile plan status with the actual repository: inspect implementation, tests, documentation and Git status. Status markers are progress hints, not proof that work is implemented or committed. Do not redo verified work; do not trust unchecked boxes blindly.
4. **Before implementing the selected phase**, search open GitHub issues for a suitable issue representing that phase.
5. Reuse an accurate open issue. If none exists, create a phase issue autonomously before implementation; never ask merely for permission to create it.
6. Never edit metadata or state of a reused issue; comments are allowed. Agent-created phase issues may receive progress updates and may be closed after the phase gate succeeds.
7. Record the issue reference in the plan or progress report, then start the first pending, unblocked work package.

## Repeated work-package loop

For each work package:

1. Set its status to `[-]` when beginning, if the plan is a writable file.
2. Inspect relevant implementation, tests, configuration and documentation.
3. Implement the smallest complete change satisfying the acceptance criteria.
4. Review the diff before testing for scope, correctness and unintended changes.
5. Run relevant tests and non-mutating checks. Use the project's actual commands; do not assume targets exist. Run broader checks at meaningful integration boundaries.
6. Fix failures and repeat affected checks. Do not bypass failing tests.
7. Once the work package is implemented and locally verified, update its plan checkbox to `[x]` **before committing**. Include the plan update in the same commit as the implementation it describes.
8. Review the combined code-and-plan diff, stage only work-package changes and create one coherent Conventional Commit referencing the phase issue.
9. If the commit cannot be created, do not leave the work package marked complete: restore its status to `[-]` or `[~]` and explain the blocker.
10. Add a concise progress comment to the phase issue when useful. Never edit a reused issue's fields or state.

A work package may combine closely related small tasks. Avoid both giant commits and artificial micro-commits.

## Status markers

Use these markers directly in phase and work-package headings:

- `[ ]` pending
- `[-]` in progress
- `[x]` completed
- `[~]` deferred or blocked

A work package may be marked `[x]` after its acceptance criteria pass local verification; commit the code and plan update together. A phase must remain `[-]` until all selected work packages are complete, the phase changes are pushed and relevant CI is green. Only then mark the phase `[x]`. Use `[~]` with a short explanation for blocked/deferred work; never mark incomplete work complete.

If the plan was pasted into the prompt rather than supplied as a writable file, maintain progress in the session and provide an updated plan/status in the final response. Do not create a second tracking file unless explicitly requested.

## Push cadence and CI gate

- Track coherent commits since the last successful push.
- Push after approximately 3–6 commits, or at phase completion if earlier. Do not exceed six commits solely to preserve batching.
- A selected phase boundary is a push boundary, even if it produced fewer than three commits.
- Push only intended work; never include unrelated user changes.
- After each push, monitor the relevant GitHub Actions workflows until they reach a definitive result.
- If CI fails, inspect logs, fix the cause, run local checks, commit the correction, push and monitor again.
- Do not start dependent work or mark the phase complete until relevant CI is green.
- If two repair cycles fail to produce a clear path, or CI is non-reproducible and requires user input, stop and report the blocker.

## Phase completion

A selected phase is complete only when:
- Every selected work package and acceptance criterion is satisfied.
- Relevant local tests and checks pass.
- All phase changes, including plan status updates, are committed and pushed.
- Relevant GitHub Actions CI is green.

Then mark the phase `[x]` and commit/push that final plan status update if it was not already included in the verified phase commit. Close the phase issue only if the agent created it during this run. Never close a reused issue.

## Context handoff and plan report

When context is becoming large, before handing off, or at a phase boundary:

- Ensure the current work package status is accurate.
- Update the supplied plan file with a short `## Progress / Handoff` entry at its end: completed work, current state, next work package, relevant issue/commits/push/CI, blockers and important decisions.
- Keep the report concise and append a new dated entry rather than rewriting useful history.
- If the plan was prompt-only, provide the handoff summary in the conversation; do not invent a file path.

## Final report

Summarize completed phases/work packages, tests and checks, issue references, commits, pushes and CI results. State explicitly if any part remains incomplete.
