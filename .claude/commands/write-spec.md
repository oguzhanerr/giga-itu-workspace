# /write-spec

Generate a structured PRD from a problem statement or feature idea.

## Input
The user provides: a problem statement, feature idea, or rough description. Ask for the product name if not clear.

## Output
A PRD document saved to `2_for-review/prd-<product-slug>-<feature-slug>.md` with:

- **Overview** — one paragraph summary of the problem and proposed solution
- **User stories** — written as "As a [user], I want to [action] so that [outcome]"
- **Requirements** — functional requirements as a prioritised list (Must / Should / Nice to have)
- **Out of scope** — explicitly what this spec does not cover
- **Success metrics** — 2–3 measurable outcomes that define success
- **Open questions** — anything unresolved that needs a decision before development

## Rules
- Keep it concise — a good spec fits on 1–2 pages
- Tie requirements back to user stories
- Flag assumptions explicitly
- Save to `2_for-review/` — do not file directly to projects/
