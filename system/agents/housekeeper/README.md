---
type: agent
name: Housekeeper Agent
scope: local
created: 2026-04-21
---

## Purpose
Maintains the vault and local data sources in sync. Runs automatically on weekdays — no manual intervention needed.

## Platform Support

| Skill | macOS | Linux | Windows |
|---|---|---|---|
| Daily assimilate | ✅ | ✅ | ✅ |
| Calendar sync (Apple) | ✅ | ❌ | ❌ |
| Calendar sync (Outlook/Google) | ✅ | ✅ | ✅ |
| Meetily export | ✅ | ✅ | ✅ |
| Scheduler | launchd | systemd (manual setup) | Task Scheduler (manual setup) |

Apple Calendar is macOS-only. Outlook and Google Calendar work everywhere. Meetily works on all platforms — the installer detects the correct database path per OS.

## Configuration
All machine-specific paths are set via environment variables or `system/config.yaml`:

| Variable | Description | Default |
|---|---|---|
| `VAULT_DIR` | Absolute path to vault root | Auto-detected from script location |
| `MEETILY_DB` | Path to Meetily SQLite database | `~/Library/Application Support/com.meetily.ai/meeting_minutes.sqlite` |
| `CLAUDE_BIN` | Path to Claude Code CLI | `~/.local/bin/claude` |

## Model Selection

Three tiers — pick based on what the job actually needs:

| Tier | Model | Use when |
|---|---|---|
| Complex planning | `claude-opus-4-7` | New system design, ambiguous requirements, multi-system changes |
| Standard execution | `claude-sonnet-4-6` | Drafting, synthesis, routing with judgement calls |
| Simple execution | `claude-haiku-4-5-20251001` | File ops, extraction, front matter updates |

| Job | Default model | Why |
|---|---|---|
| Daily assimilate (quiet day) | `claude-haiku-4-5-20251001` | Read/write only — no reasoning needed |
| Daily assimilate (system changed) | `claude-sonnet-4-6` | Auto-detected: agent files or CLAUDE.md modified today |

The script selects Haiku or Sonnet automatically. Override via `DAILY_ASSIMILATE_MODEL` env var.

**Convention**: When adding a new scheduled job that invokes Claude, document its model choice here with a one-line reason.

## Scheduled Jobs

| Job | Script | Schedule |
|---|---|---|
| Calendar sync | `calendar-sync.py` | Mon–Fri 08:00 & 18:00 |
| Meetily export | `meetily-export.py` | Mon–Fri 08:00 & 18:00 |
| Daily assimilate | `daily-assimilate.sh` | Mon–Fri 18:00 |

## Setup (macOS)
1. Copy `config.template.yaml` to `system/config.yaml` and fill in your values
2. Run `install-launchd.sh` to register all scheduled jobs

## Setup (Linux/Windows)
1. Copy `config.template.yaml` to `system/config.yaml` and fill in your values
2. Set `VAULT_DIR` as an environment variable, or rely on auto-detection
3. Register `daily-assimilate.sh` with your system scheduler (systemd/Task Scheduler)
4. Calendar sync and Meetily export are not available — skip or implement alternatives
