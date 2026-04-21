#!/bin/bash
# Obsidian tasks/ watcher — called by LaunchAgent
# Passes each changed .md file path to clickup_sync.py

VAULT="${VAULT_DIR:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
TASKS_DIR="$VAULT/tasks"
SCRIPT="$(dirname "$0")/clickup_sync.py"

FSWATCH="$(which fswatch 2>/dev/null || echo /opt/homebrew/bin/fswatch)"

exec "$FSWATCH" \
  --event Created \
  --event Updated \
  --event Renamed \
  --latency 1 \
  --extended \
  --exclude '\.DS_Store' \
  --exclude '\.sync' \
  --include '\.md$' \
  -0 "$TASKS_DIR" \
  | xargs -0 -n1 python3 "$SCRIPT"
