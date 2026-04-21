---
type: agent
name: ClickUp Sync Agent
scope: local
created: 2026-04-21
---

## Purpose
Keeps Obsidian task notes in sync with ClickUp. Watches the `tasks/` folder for file changes and creates or updates ClickUp tasks automatically.

## Access
- Obsidian vault `tasks/` folder (via fswatch)
- ClickUp API (token in launchd plist environment variable)

## Skills
- Create a new ClickUp task when a task note has no `clickup_id`
- Update status, priority, and due date when a task note is modified
- Route tasks to the correct ClickUp list based on `clickup_list` front matter

## Trigger
Event-driven — fires on file create/update/rename in `tasks/`. Always running as a background process.

## Files
- `clickup_watch.sh` — fswatch watcher, passes changed files to sync script
- `clickup_sync.py` — reads front matter, calls ClickUp API

## launchd plist
`com.oz.obsidian-clickup.plist` — `RunAtLoad: true`, `KeepAlive: true`

## Setup
1. Add `CLICKUP_TOKEN` to the plist environment variables
2. `launchctl load ~/Library/LaunchAgents/com.oz.obsidian-clickup.plist`
