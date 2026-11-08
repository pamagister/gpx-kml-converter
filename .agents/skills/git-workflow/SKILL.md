---
name: git-workflow
description: Repository Git and GitHub conventions for issue lookup and creation, safe staging, Conventional Commits, push batching and GitHub Actions CI.
---

# Git and GitHub Workflow

Use this skill whenever a task involves GitHub issues, staging, commits, branches, pushes or Actions.

## Safety

- Inspect `git status` and the current branch before changing Git state.
- Preserve unrelated and pre-existing user changes. Never use indiscriminate staging.
- Stage only changes belonging to the authorized task or work package.
- Never amend existing commits, rewrite history, force-push or delete branches unless explicitly authorized.
- Never commit secrets, credentials, tokens or temporary/generated artifacts unrelated to the task.

## Issues

- Search open issues in the target repository before creating one. Reuse an issue only when it accurately represents the requested feature or Autopilot phase.
- If no suitable issue exists in Feature mode or Autopilot, create one autonomously; do not interrupt the user just to ask permission.
- Keep new issue titles concise and bodies actionable: context, expected outcome, scope and acceptance criteria.
- Apply existing repository labels only when they clearly fit. Do not invent a new label taxonomy.
- **Never edit an issue that already existed before this task**: do not change its title, body, labels, assignees, milestone or state. Adding comments is allowed.
- For an issue created by the agent during this task, comments and appropriate progress updates are allowed. In Autopilot, close an agent-created phase issue only after its phase is fully implemented, committed, pushed and its relevant CI is green.
- Do not close reused issues. A commit alone is not grounds to close an issue.

## Commits

Use Conventional Commits:

```text
<type>(<scope>): <imperative description>

<optional body>

Refs #<issue-number>
```

Use `Fixes #N` only when the commit itself fully resolves the issue and the workflow authorizes closing it. Otherwise use `Refs #N`.

Common types:
- `feat`: functionality
- `fix`: bug fix
- `refactor`: restructuring without behavior change
- `test`: tests
- `docs`: documentation
- `build`: build system or dependencies
- `ci`: CI configuration
- `chore`: maintenance

Keep each commit coherent, verified and focused. Do not bundle unrelated work.

## Push and CI

- Push only when the selected workflow authorizes it.
- In Autopilot, batch approximately 3–6 coherent commits; push earlier when a phase ends, and never exceed six commits just to preserve batching.
- After each push, identify the relevant GitHub Actions runs for the pushed commit and wait for a definitive result.
- Do not treat pending, missing or timed-out results as success.
- If CI fails, inspect logs, reproduce locally where possible, fix the cause, run the relevant checks, commit the correction, push and verify CI again.
- Do not continue with dependent work until relevant CI is green.
- If two repair cycles fail to produce a clear, actionable path, stop and report the blocker rather than looping indefinitely.

## Reporting

Report issue numbers, commit hashes, push status and actual CI results. Clearly distinguish local checks from remote CI.
