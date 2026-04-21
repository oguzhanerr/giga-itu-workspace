#!/usr/bin/env python3
"""
Polls Meetily's SQLite DB for completed meetings, merges content into the
matching calendar stub in meetings/ (or creates a new file if no stub exists),
creates task notes from action items, and updates the daily brief.
"""

import os
import platform
import sqlite3
import json
import re
import sys
from datetime import datetime
from pathlib import Path

VAULT       = Path(os.environ["VAULT_DIR"]) if "VAULT_DIR" in os.environ else Path(__file__).parents[3]

def _default_meetily_db() -> Path:
    _os = platform.system()
    if _os == "Darwin":
        return Path.home() / "Library/Application Support/com.meetily.ai/meeting_minutes.sqlite"
    elif _os == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
        return base / "com.meetily.ai/meeting_minutes.sqlite"
    else:  # Linux
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        return base / "com.meetily.ai/meeting_minutes.sqlite"

DB          = Path(os.environ.get("MEETILY_DB", str(_default_meetily_db())))
MEETINGS_DIR = VAULT / "meetings"
TASKS_DIR   = VAULT / "tasks"
DAILY_BRIEF = VAULT / "0_daily-brief/daily-brief.md"
STATE_FILE  = Path.home() / ".meetily-exported-ids"


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9 ]", "", text.lower())
    return re.sub(r"\s+", "-", text.strip())[:60].rstrip("-")


def parse_action_items(raw: str) -> list[str]:
    if not raw:
        return []
    try:
        items = json.loads(raw)
        if isinstance(items, list):
            return [str(i).strip() for i in items if str(i).strip()]
    except (json.JSONDecodeError, ValueError):
        pass
    lines = re.split(r"\n|•", raw)
    cleaned = []
    for line in lines:
        line = re.sub(r"^[\s\-\*\d\.]+", "", line).strip()
        if line:
            cleaned.append(line)
    return cleaned


def extract_summary_markdown(result_json: str) -> str:
    """Pull the markdown field from summary_processes.result JSON."""
    if not result_json:
        return ""
    try:
        data = json.loads(result_json)
        return data.get("markdown", "")
    except (json.JSONDecodeError, ValueError):
        return result_json


def find_stub(mtg_date: str, meetily_title: str):
    """
    Find an existing calendar stub for the same date.
    Tries exact match first, then picks the stub with the most title-word overlap.
    """
    safe = re.sub(r'[\/\\:*?"<>|]', "-", meetily_title)
    exact = MEETINGS_DIR / f"{mtg_date} {safe}.md"
    if exact.exists():
        return exact

    candidates = [p for p in MEETINGS_DIR.glob(f"{mtg_date} *.md") if p.is_file()]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    # Score by word overlap with Meetily title
    title_words = set(re.findall(r"[a-z]+", meetily_title.lower()))
    best, best_score = None, -1
    for p in candidates:
        stub_words = set(re.findall(r"[a-z]+", p.stem.lower()))
        score = len(title_words & stub_words)
        if score > best_score:
            best, best_score = p, score
    return best


def merge_into_stub(stub_path: Path, summary_md: str, action_items: list[str]) -> None:
    """Append Meetily summary into the existing stub without overwriting user notes."""
    content = stub_path.read_text()

    # Don't merge twice
    if "## Meetily Summary" in content:
        return

    # Build the block to append
    lines = ["\n## Meetily Summary\n", summary_md.strip()]
    if action_items:
        lines += ["\n## Action Items from Transcript\n"]
        for item in action_items:
            lines.append(f"- {item}")

    stub_path.write_text(content.rstrip() + "\n" + "\n".join(lines) + "\n")


def write_new_note(path: Path, mtg_date: str, summary_md: str) -> None:
    path.write_text(f"**Date:** {mtg_date}\n\n{summary_md}\n")


def write_task_note(path: Path, action: str, note_ref: str, mtg_date: str, title_tag: str, today: str) -> None:
    path.write_text(f"""---
status: todo
priority: medium
due:
created: {today}
completed:
source: "{note_ref}"
clickup_id:
clickup_list: sprint
tags:
  - task
  - meeting
  - {title_tag}
---

## Context
Action item from {note_ref} ({mtg_date}).

## Next action
{action}

## Log
- {today}: Task created from {note_ref}
""")


def append_to_daily_brief(note_ref: str, mtg_date: str, n_tasks: int) -> None:
    if not DAILY_BRIEF.exists():
        return
    content = DAILY_BRIEF.read_text()
    entry = f"\n- Meeting exported: {note_ref} — {n_tasks} task(s) created ({mtg_date})"
    if "## Recently Processed" in content:
        content = content.replace("## Recently Processed",
                                  f"## Recently Processed\n{entry}", 1)
    else:
        content = content.rstrip() + "\n\n## Recently Processed" + entry + "\n"
    DAILY_BRIEF.write_text(content)


def load_state() -> set:
    return set(STATE_FILE.read_text().strip().splitlines()) if STATE_FILE.exists() else set()


def save_state(ids: set) -> None:
    STATE_FILE.write_text("\n".join(sorted(ids)) + "\n")


def main() -> None:
    if not DB.exists():
        print("Meetily DB not found — skipping.", file=sys.stderr)
        return

    exported = load_state()
    today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT m.id, m.title, m.created_at,
               COALESCE(sp.result, '') AS summary_result
        FROM meetings m
        LEFT JOIN summary_processes sp ON m.id = sp.meeting_id
        WHERE sp.status = 'completed'
        ORDER BY m.created_at ASC
    """)

    for row in cur.fetchall():
        mid = row["id"]
        if mid in exported:
            continue

        title       = row["title"]
        mtg_date    = row["created_at"][:10]
        summary_md  = extract_summary_markdown(row["summary_result"])

        # Get action items from transcripts
        cur2 = conn.cursor()
        cur2.execute(
            "SELECT action_items FROM transcripts WHERE meeting_id=? AND action_items IS NOT NULL AND action_items != ''",
            (mid,),
        )
        all_items: list[str] = []
        for trow in cur2.fetchall():
            all_items.extend(parse_action_items(trow[0]))

        # Find or create the target file
        stub = find_stub(mtg_date, title)
        if stub:
            merge_into_stub(stub, summary_md, all_items)
            target_path = stub
            print(f"Merged into: {stub.name}")
        else:
            safe_title = re.sub(r'[\/\\:*?"<>|]', "-", title)
            target_path = MEETINGS_DIR / f"{mtg_date} {safe_title}.md"
            write_new_note(target_path, mtg_date, summary_md)
            print(f"Created: {target_path.name}")

        note_ref  = f"[[{target_path.stem}]]"
        title_tag = slugify(title)
        tasks_created = 0

        if all_items:
            for action in all_items:
                task_slug = slugify(action)
                if not task_slug:
                    continue
                task_path = TASKS_DIR / f"{task_slug}.md"
                if task_path.exists():
                    task_path = TASKS_DIR / f"{task_slug}-{mtg_date}.md"
                write_task_note(task_path, action, note_ref, mtg_date, title_tag, today)
                tasks_created += 1
        else:
            slug = f"review-{slugify(title)}-{mtg_date}"
            task_path = TASKS_DIR / f"{slug}.md"
            write_task_note(task_path, "Review meeting notes and follow up on commitments.",
                            note_ref, mtg_date, title_tag, today)
            tasks_created = 1

        append_to_daily_brief(note_ref, mtg_date, tasks_created)
        exported.add(mid)

    conn.close()
    save_state(exported)


if __name__ == "__main__":
    main()
