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
| Calendar sync | ✅ (Apple Calendar via EventKit) | ❌ | ❌ |
| Meetily export | ✅ (Meetily is macOS-only) | ❌ | ❌ |
| Scheduler | launchd | systemd (manual setup) | Task Scheduler (manual setup) |

Calendar sync and Meetily export are macOS-only. Linux/Windows team members can still use daily assimilate — they'll need to set up their own scheduler instead of using `install-launchd.sh`.

## Configuration
All machine-specific paths are set via environment variables or `system/config.yaml`:

| Variable | Description | Default |
|---|---|---|
| `VAULT_DIR` | Absolute path to vault root | Auto-detected from script location |
| `MEETILY_DB` | Path to Meetily SQLite database | `~/Library/Application Support/com.meetily.ai/meeting_minutes.sqlite` |
| `CLAUDE_BIN` | Path to Claude Code CLI | `~/.local/bin/claude` |

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
