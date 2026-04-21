# /assimilate

> Note: this is not a registered Claude Code slash command. It is a reference doc Claude reads and follows manually when the user asks to assimilate. When asked, read this file and execute the steps.


Review the current session and persist anything worth remembering to durable files.

## What to look for

1. **Corrections**: Anything the user corrected you on (wrong folder, wrong tone, wrong assumption)
2. **New conventions**: Naming patterns, workflow changes, structural decisions
3. **New context**: Key facts about projects or people that came up and aren't already documented
4. **Preferences confirmed**: Communication style, formatting, tool usage patterns
5. **Mistakes to avoid**: Things that went wrong and how to prevent them next time

## How to persist

1. Read `CLAUDE.md` and any relevant command files in `.claude/commands/`
2. Check if the learning already exists - don't duplicate
3. If it updates an existing entry, edit it in place
4. If it's new, add it to the right file:
   - Command-specific lessons → `.claude/commands/<name>.md`
   - Project-specific conventions → that project's `CLAUDE.md` if it has one
   - Vault-wide patterns → root `CLAUDE.md`

## Rules

- Only persist things that are **stable and confirmed** - not in-progress experiments
- Don't persist session-specific context (current task state, temporary decisions)
- Be concise - one line per lesson where possible
- Tell the user what you wrote and where
