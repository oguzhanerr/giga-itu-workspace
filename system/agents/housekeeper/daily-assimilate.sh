#!/bin/bash
# End-of-day retrospective — reviews the vault and persists stable learnings.

VAULT="${VAULT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
CLAUDE="${CLAUDE_BIN:-$HOME/.local/bin/claude}"

# Complexity heuristic: if system agents or CLAUDE.md changed today → Sonnet (conventions may need updating)
# Otherwise → Haiku (simple read/write, no reasoning needed)
# Manual override always wins via DAILY_ASSIMILATE_MODEL env var
if [ -n "${DAILY_ASSIMILATE_MODEL}" ]; then
    MODEL="$DAILY_ASSIMILATE_MODEL"
else
    SYSTEM_CHANGES=$(find "$VAULT/system/agents" "$VAULT/CLAUDE.md" -type f -mtime -1 2>/dev/null | wc -l | tr -d ' ')
    if [ "$SYSTEM_CHANGES" -gt 0 ]; then
        MODEL="claude-sonnet-4-6"
    else
        MODEL="claude-haiku-4-5-20251001"
    fi
fi

"$CLAUDE" -p "You are running an end-of-day retrospective for Oz's personal vault. Your job is to review what happened today and persist any stable learnings to memory files or CLAUDE.md.

Working directory: $VAULT

Steps:
1. Run \`date\` to confirm today's date.
2. Read \`0_daily-brief/daily-brief.md\` to see what was processed today.
3. Read today's daily note at \`1_inbox/YYYY-MM-DD.md\` (use the actual date).
4. Read \`CLAUDE.md\` to understand existing conventions.
5. Read all files in \`CLAUDE.md\` Working Conventions section and \`system/agents/\` to understand existing agents and conventions.
6. Identify anything worth persisting: corrections made today, new conventions established, workflow improvements, new context about projects or people, preferences confirmed.
7. Write new or updated content to CLAUDE.md Working Conventions if applicable.
8. If anything should update agent definitions in \`system/agents/\`, edit them.
9. Write a brief log entry to \`0_daily-brief/daily-brief.md\` under the Changelog section: \"HH:MM — End-of-day assimilate: [one line summary of what was persisted, or 'nothing new to persist']\"

Rules:
- Only persist stable, confirmed patterns — not in-progress experiments or today's task state.
- Do not duplicate existing conventions.
- Be concise — one line per lesson where possible.
- If nothing new happened worth persisting, just log that and exit." \
  --model "$MODEL" \
  --allowedTools Bash,Read,Write,Edit,Glob,Grep \
  --add-dir "$VAULT"
