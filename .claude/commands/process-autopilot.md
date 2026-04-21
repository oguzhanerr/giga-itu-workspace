# /process-autopilot

Hands-free processing of the vault. Reads daily notes, extracts tasks, updates the daily brief, and flags anything needing input. Questions go to the daily brief — not the terminal.

## Steps

Follow `system/process-workflow.md` exactly. Summary:

1. **Establish the date** — run `date` in terminal. Do not assume.
2. **Check state** — read `0_daily-brief/daily-brief.md`. If stale or missing, build fresh. Read today's daily note (`1_inbox/YYYY-MM-DD.md`).
3. **Scan tasks** — check `tasks/` for overdue, due today, or stale waiting items.
4. **Process daily note** — follow extraction rules in `system/processing-rules.md`. Create task notes in `tasks/`. Route reflective content to `journal/` if journal module applies.
5. **Update daily brief** — priorities, tasks needing attention, questions for user, recently completed, changelog entry with timestamp.
6. **Check for-review staleness** — items 2+ days old in `2_for-review/` move to `2_for-review/stale/` and get flagged in the brief.

## Rules

- Never overwrite or delete user content in daily notes
- Never mark tasks done unless user has confirmed
- All output goes to `0_daily-brief/daily-brief.md` — do not ask questions in the terminal
- Check for existing tasks before creating new ones (match by filename or tags)
- Convert relative dates to YYYY-MM-DD using `date` — never do mental arithmetic
- Archive daily notes older than 7 days to `1_inbox/archive/`

## Task rejection patterns (learned)

- If a task depends on another structural item being set up first (e.g. attachments folder), skip it and note the dependency in the brief
- If the user already has a document started for something, do not create a task for the initial draft — create for the revision/next step only
- If an outreach/intro has already happened, reflect that in task status (in-progress) and next action
