---
type: skill
name: PM Artefacts
agent: product-manager
created: 2026-04-21
---

## Purpose
Generate product management documents from structured inputs. All output goes to `2_for-review/` before being filed.

## Commands

| Command | Output |
|---|---|
| `/write-spec` | PRD with user stories, requirements, success metrics |
| `/roadmap-update` | Roadmap in Now/Next/Later, quarterly, or OKR format |
| `/stakeholder-update` | Tailored update for exec, engineering, or customers |
| `/synthesize-research` | Structured insights from interviews or survey data |
| `/competitive-brief` | Competitor matrix and differentiation summary |
| `/metrics-review` | Metrics analysis with trends and recommended actions |

Full command definitions in `.claude/commands/`.

## Model

`claude-sonnet-4-6` (session default) — drafting and synthesis requires judgement. Override with `--model` if running non-interactively.

## Output conventions
All artefacts stage to `2_for-review/` first. Once confirmed, file to `projects/<product>/`.
