# /competitive-brief

Produce a competitive analysis brief.

## Input
The user provides: a product or feature area to analyse, and optionally a list of competitors. If no competitors are given, suggest likely ones based on the product context.

## Output
A competitive brief saved to `2_for-review/competitive-brief-<product>-<date>.md` with:

- **Market context** — one paragraph on the competitive landscape
- **Competitor matrix** — table comparing key dimensions (features, pricing, target audience, positioning)
- **Strengths & gaps** — what competitors do well and where they fall short
- **Our differentiation** — where the Giga product has a distinct angle
- **Implications** — 2–3 product or positioning decisions this analysis suggests

## Rules
- Focus on signal, not exhaustive coverage — 3–5 competitors is enough
- Flag where information is inferred vs confirmed
- Tie conclusions back to product decisions, not just observations
- Save to `2_for-review/` — user reviews before sharing
