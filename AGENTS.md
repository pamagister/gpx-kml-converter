# Repository Instructions

These rules apply to this Python project. Keep changes focused and follow the existing architecture.

## Python conventions

- Target Python 3.11 as declared in `pyproject.toml`.
- Follow PEP 8 and the repository's Ruff configuration: 4-space indentation, double quotes, 100-character line length.
- Use `snake_case` for packages, modules, functions and variables; `PascalCase` for classes; and `UPPER_SNAKE_CASE` for constants.
- Use `snake_case` for importable Python names. Use `kebab-case` for distribution/repository names, CLI commands and documentation paths.
- Prefer descriptive names, type hints on public function signatures, explicit imports, context managers and focused functions.
- Add or update deterministic pytest tests for behavior changes, bug fixes and important edge cases.

## Project tooling

- Use `uv` for dependency and environment management. Declare dependencies in `pyproject.toml`.
- Use Ruff for linting and formatting, and pytest for tests. Follow the existing configuration rather than introducing alternative tools.
- Inspect the Makefile before using a target. Relevant targets:
  - `make lint`: Ruff lint and format checks.
  - `make test`: lint plus the test suite and coverage reports.
  - `make fmt`: mutating formatting/fix operations and documentation synchronization.
  - `make precommit`: runs formatting, tests and dependency checks; it is mutating and may install a tool.
- Do not run mutating convenience targets merely as a substitute for understanding what they do.

## Generated documentation

- `docs/index.md` is the source for `README.md`. Never edit `README.md` directly.
- After changing `docs/index.md`, run `make syncdocs` when appropriate.
- Check existing generation scripts before editing generated files.

## Agent workflow routing

Choose the workflow from the user's requested scope, not from whether they know or use the internal mode name.

- **Task mode:** A bounded change such as a review, typo fix or small documentation adjustment. Load `workflow-standard`.
- **Feature mode:** One self-contained feature or bug fix not framed as execution of a plan phase. Load `workflow-standard`.
- **Autopilot:** Whenever the user asks to implement, execute or continue a plan, or names one or more phases/work packages from a plan. This includes a single selected phase. Phrases such as "implement the first phase", "execute phase 2", "continue plan.md" or "implement autonomously" are sufficient; the user does not need to say "Autopilot". Load `workflow-autopilot` and `git-workflow`.

A plan-phase request always takes precedence over the ordinary single-feature workflow, even when the selected phase is the only requested scope. Execute only the phase/work packages the user selected; do not continue into later phases without authorization.

Load the supporting skills as needed:
- `workflow-standard`: Task and Feature modes.
- `workflow-autopilot`: plan and phase execution.
- `git-workflow`: Git, GitHub issues, commits, pushes and CI.
- `mission-planning`: turn a mission or external specification into one executable plan.
