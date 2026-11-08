---
name: mission-planning
description: Convert a user mission, rough requirements or an external project plan into one concise, executable Markdown implementation plan for an autonomous coding agent.
---

# Mission Planning

Your task is to turn the supplied mission into a clear implementation plan. Do not implement the plan.

## Understand the mission

- Identify the objective, expected outcomes, functional and non-functional requirements, constraints, dependencies and risks.
- Separate mandatory scope from optional ideas and explicitly deferred work.
- Identify architectural and interface decisions that materially affect implementation.
- Resolve important ambiguity with the user; do not silently invent product requirements.
- Prefer the simplest design that satisfies the mission.

## Produce one plan

Produce one self-contained Markdown plan, ready to paste into an agent prompt or save at any user-chosen path. Do not require or generate a separate tasklist, progress file or repository instruction file.

Include only sections that add value:
1. Objective and desired outcome.
2. Scope, constraints and explicit non-goals.
3. Architecture and decisions (including rationale where useful).
4. Phases containing coherent work packages.
5. Acceptance criteria and verification expectations.
6. Dependencies, risks and unresolved questions.

## Work-package quality

- Organize work in a logical dependency order.
- Make each work package small enough to implement, review, test and commit independently, but avoid trivial micro-tasks.
- State observable acceptance criteria, not implementation narration.
- Identify integration boundaries and meaningful phase gates.
- Include tests, documentation and migration considerations where relevant.
- Do not prescribe details the implementation agent can safely decide.
- Do not duplicate repository-wide coding or Git rules in the plan.

## Progress-ready format

Put status markers directly in phase and work-package headings:

- `[ ]` pending
- `[-]` in progress
- `[x]` completed
- `[~]` deferred or blocked

Example:

```markdown
## Phase 1: Foundation [ ]

### 1.1 Establish the data model [ ]
- Acceptance criteria:
  - ...

### 1.2 Add validation [ ]
- Acceptance criteria:
  - ...
```

The plan must be usable whether pasted into a prompt or saved as a Markdown file. Its path is supplied by the user, not assumed.

## Review before delivery

Check that all requirements are represented, dependencies are ordered, acceptance criteria are testable, scope is bounded, and the plan can be executed without unnecessary clarification. Present remaining assumptions and open questions separately from settled decisions.
