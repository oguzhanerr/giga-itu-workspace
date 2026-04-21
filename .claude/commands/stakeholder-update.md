# /stakeholder-update

Draft a tailored update for a specific audience.

## Input
The user provides: what to communicate and who the audience is. Audience options:
- **Executive** — high-level, outcome-focused, no technical detail
- **Engineering** — technical context, dependencies, decisions needed
- **Customer** — benefit-focused, plain language, no internal jargon

## Output
A stakeholder update saved to `2_for-review/stakeholder-update-<audience>-<date>.md` with:

- **Subject / headline** — one sentence summary
- **Status** — on track / at risk / blocked
- **Key updates** — 3–5 bullet points relevant to this audience
- **Decisions needed** (if any)
- **Next milestone**

## Rules
- Adapt tone and detail level strictly to the audience
- Pull relevant context from the vault if available (tasks, project notes, daily brief)
- Keep it short — stakeholder updates should be scannable in under 2 minutes
- Save to `2_for-review/` — user reviews before sending
