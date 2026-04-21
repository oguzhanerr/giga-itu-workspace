# /metrics-review

Review and analyse product performance metrics.

## Input
The user provides: metrics data, a dashboard screenshot, or a description of current numbers. Specify the product and time period if relevant.

## Output
A metrics review saved to `2_for-review/metrics-review-<product>-<date>.md` with:

- **Summary** — one paragraph on overall product health
- **Key metrics** — table of the most important metrics with current value, trend, and target
- **What's working** — metrics trending positively with brief explanation
- **Watch list** — metrics that are flat or declining and why they matter
- **Recommended actions** — 2–3 specific things to do based on the data
- **Open questions** — gaps in the data or things that need further investigation

## Rules
- Focus on actionable insight, not just reporting numbers
- Distinguish between leading indicators (predict future) and lagging indicators (measure past)
- Flag if data is incomplete or the sample size is too small to draw conclusions
- Pull relevant context from the vault if available (PRDs, task notes, sprint outcomes)
- Save to `2_for-review/` — user reviews before sharing
