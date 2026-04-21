---
type: agent
name: Product Manager Agent
scope: local + cloud
created: 2026-04-21
---

## Purpose
Supports the full PM workflow — writing specs, managing roadmaps, communicating with stakeholders, synthesising research, analysing competitors, and tracking metrics. ClickUp sync keeps the vault and ClickUp in sync automatically.

---

## Skills

### PM Artefacts → `skills/pm-artefacts/`
Generate PM documents from structured inputs. Commands: `/write-spec`, `/roadmap-update`, `/stakeholder-update`, `/synthesize-research`, `/competitive-brief`, `/metrics-review`. All output stages to `2_for-review/`.

**Example:**
```
/write-spec

We need a way for school connectivity administrators to simulate mobile coverage
before deploying infrastructure. Target users are government MoE officials in
low-connectivity regions.
```

### ClickUp Sync → `skills/clickup-sync/`
Event-driven automation. Watches `tasks/` for file changes and syncs to ClickUp automatically — no manual action needed.

```yaml
# In any task note front matter:
clickup_id: 86c8z0x6z        # auto-filled on first sync
clickup_list: sprint          # or: backlog, none
status: in-progress
priority: high
due: 2026-04-30
```

---

## Vault Conventions

| Output type | Destination |
|---|---|
| All PM artefacts | `2_for-review/` → confirm → `projects/<product>/` |
| Task notes | `tasks/` → auto-synced to ClickUp |

---

## Adding New Skills
Create a `skills/<skill-name>/README.md` describing the skill's purpose, entry points, and output conventions. Add a reference here.
