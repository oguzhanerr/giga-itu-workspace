# /roadmap-update

Plan and reprioritise the product roadmap.

## Input
The user provides: current backlog items, priorities, or a description of what changed. Ask for the format preference if not specified (Now/Next/Later, quarterly, OKR-aligned).

## Output
A roadmap document saved to `2_for-review/roadmap-update-<date>.md` with:

- **Now** — in active development this sprint/cycle
- **Next** — committed for the next cycle
- **Later** — backlog, not yet scheduled
- **Dropped / Deprioritised** — explicitly called out with reason

Or quarterly/OKR format if requested.

## Rules
- Pull current task and project state from the vault if relevant (read `tasks/`, `projects/`)
- Flag any dependencies or blockers between items
- Keep each item to one line — details live in the task/PRD
- Save to `2_for-review/` — do not overwrite any existing roadmap directly
