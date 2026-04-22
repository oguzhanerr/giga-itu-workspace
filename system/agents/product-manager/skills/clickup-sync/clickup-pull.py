#!/usr/bin/env python3
"""
ClickUp → Obsidian pull sync.
Fetches tasks from configured ClickUp lists and updates vault front matter.

Usage:
  python3 clickup-pull.py [--create-missing]

  --create-missing  also create vault task notes for ClickUp tasks with no match

Config (env vars or system/config.yaml):
  CLICKUP_TOKEN            — API token
  CLICKUP_SPRINT_LIST_ID   — current sprint list ID
  CLICKUP_SPRINT_NAME      — display name, e.g. S7
  CLICKUP_BACKLOG_LIST_IDS — JSON dict: {"mobile-simulation-tool": "id", ...}
                             OR individual config.yaml keys: clickup_backlog_<project>: <id>
"""

import os
import sys
import re
import json
import logging
from pathlib import Path
from datetime import datetime
import urllib.request
import urllib.error

# ── Config ────────────────────────────────────────────────────────────────────

VAULT     = Path(os.environ.get("VAULT_DIR", str(Path(__file__).parents[4])))
TASKS_DIR = VAULT / "tasks"


def _load_config() -> dict:
    p = VAULT / "system/config.yaml"
    cfg = {}
    if p.exists():
        for line in p.read_text().splitlines():
            m = re.match(r"^([\w-]+):\s*(.+)", line)
            if m:
                cfg[m.group(1)] = m.group(2).strip()
    return cfg


_cfg = _load_config()


def _get(env_key: str, cfg_key: str = "", default: str = "") -> str:
    return os.environ.get(env_key) or _cfg.get(cfg_key or env_key.lower(), default)


TOKEN         = _get("CLICKUP_TOKEN",          "clickup_token")
_SPRINT_ID    = _get("CLICKUP_SPRINT_LIST_ID", "clickup_sprint_list_id")
_SPRINT_NAME  = _get("CLICKUP_SPRINT_NAME",    "clickup_sprint_name", "sprint")
TEAM_ID       = _get("CLICKUP_TEAM_ID",        "clickup_team_id")

# Backlog list IDs: JSON env var → config.yaml clickup_backlog_* keys
_bl_json = os.environ.get("CLICKUP_BACKLOG_LIST_IDS")
if _bl_json:
    BACKLOG_IDS: dict = json.loads(_bl_json)
else:
    BACKLOG_IDS = {
        k[len("clickup_backlog_"):].replace("_", "-"): v
        for k, v in _cfg.items()
        if k.startswith("clickup_backlog_")
    }

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    filename=os.path.expanduser("~/Library/Logs/obsidian-clickup-pull.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ── Maps ──────────────────────────────────────────────────────────────────────

STATUS_FROM_CU = {
    "to do":       "todo",
    "in progress": "in-progress",
    "done":        "done",
    "cancelled":   "cancelled",
    "closed":      "done",
    "complete":    "done",
}

PRIORITY_FROM_CU = {1: "urgent", 2: "high", 3: "medium", 4: "low"}

ACRONYMS = {"mst", "itu", "br", "fe", "ux", "mvp", "api", "crm", "pm", "sdk"}

# ── ClickUp API ───────────────────────────────────────────────────────────────


def cu_get(path: str) -> dict | None:
    url = f"https://api.clickup.com/api/v2{path}"
    req = urllib.request.Request(url, headers={"Authorization": TOKEN})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        logging.error(f"GET {path} → {e.code}: {e.read().decode()[:200]}")
        return None


def resolve_sprint() -> tuple:
    """
    Return (sprint_list_id, sprint_name).
    If CLICKUP_TEAM_ID is set, fetches the active sprint from ClickUp Spaces → Folders → Lists
    and picks the list whose name looks most like a sprint (contains 'sprint' case-insensitive,
    or is the most recently created list with sprint-like naming).
    Falls back to configured CLICKUP_SPRINT_LIST_ID if API lookup fails or team ID not set.
    """
    if not TEAM_ID:
        return _SPRINT_ID, _SPRINT_NAME

    # Fetch all spaces for the team
    data = cu_get(f"/team/{TEAM_ID}/space?archived=false")
    if not data:
        return _SPRINT_ID, _SPRINT_NAME

    best_id, best_name, best_order = "", "", -1

    for space in data.get("spaces", []):
        folders = cu_get(f"/space/{space['id']}/folder?archived=false") or {}
        for folder in folders.get("folders", []):
            lists = cu_get(f"/folder/{folder['id']}/list?archived=false") or {}
            for lst in lists.get("lists", []):
                name = lst.get("name", "")
                if "sprint" in name.lower():
                    # Prefer higher orderindex (more recent sprint)
                    order = int(lst.get("orderindex", 0))
                    if order > best_order:
                        best_id, best_name, best_order = lst["id"], name, order

    if best_id:
        logging.info(f"Auto-detected sprint: {best_name} ({best_id})")
        return best_id, best_name

    logging.warning("Sprint auto-detect found nothing — falling back to configured ID")
    return _SPRINT_ID, _SPRINT_NAME


def fetch_list_tasks(list_id: str) -> list:
    tasks, page = [], 0
    while True:
        data = cu_get(f"/list/{list_id}/task?page={page}&include_closed=true")
        if not data:
            break
        batch = data.get("tasks", [])
        tasks.extend(batch)
        if data.get("last_page", True) or not batch:
            break
        page += 1
    return tasks


# ── Vault helpers ─────────────────────────────────────────────────────────────


def parse_frontmatter(text: str) -> tuple:
    m = re.match(r"^---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    fm: dict = {}
    for line in raw.split("\n"):
        if re.match(r"^\s{2}-", line):
            continue
        kv = re.match(r"^([\w-]+):\s*(.*)", line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip('"')
    tags_block = re.search(r"^tags:\n((?:  - .+\n?)+)", raw, re.MULTILINE)
    fm["tags"] = (
        [t.strip().lstrip("- ") for t in tags_block.group(1).strip().splitlines()]
        if tags_block else []
    )
    return fm, body


def update_field(text: str, key: str, value: str) -> str:
    return re.sub(
        rf"^({re.escape(key)}:\s*).*$",
        lambda m: f"{m.group(1)}{value}",
        text,
        flags=re.MULTILINE,
    )


def build_id_index() -> dict:
    index = {}
    for p in TASKS_DIR.glob("*.md"):
        try:
            m = re.search(r"^clickup_id:\s*(\S+)", p.read_text(), re.MULTILINE)
            if m and m.group(1) not in ("", "clickup_id:"):
                index[m.group(1)] = p
        except Exception:
            pass
    return index


def create_task_note(cu: dict, list_label: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", cu["name"].lower()).strip("-")[:60]
    path = TASKS_DIR / f"{slug}.md"
    if path.exists():
        path = TASKS_DIR / f"{slug}-{cu['id']}.md"

    due = ""
    if cu.get("due_date"):
        due = datetime.fromtimestamp(int(cu["due_date"]) / 1000).strftime("%Y-%m-%d")

    status   = STATUS_FROM_CU.get(cu.get("status", {}).get("status", "").lower(), "todo")
    prio_raw = (cu.get("priority") or {}).get("id")
    priority = PRIORITY_FROM_CU.get(int(prio_raw) if prio_raw else None, "medium")
    today    = datetime.now().strftime("%Y-%m-%d")
    desc     = (cu.get("description") or "").strip()

    path.write_text(f"""---
status: {status}
priority: {priority}
due: {due}
created: {today}
completed:
source: clickup
clickup_id: {cu['id']}
clickup_list: {list_label}
tags:
  - task
  - itu
---

## Context
Pulled from ClickUp.{(' ' + desc) if desc else ''}

## Next action


## Log
- {today}: Created from ClickUp pull (task {cu['id']}).
""")
    return path


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    create_missing = "--create-missing" in sys.argv

    if not TOKEN:
        print("CLICKUP_TOKEN not set — aborting.", file=sys.stderr)
        sys.exit(1)

    # Resolve current sprint (auto-detect if CLICKUP_TEAM_ID is set)
    SPRINT_ID, SPRINT_NAME = resolve_sprint()

    lists: list = []
    if SPRINT_ID:
        lists.append((SPRINT_ID, SPRINT_NAME))
    for project, lid in BACKLOG_IDS.items():
        lists.append((lid, "backlog"))

    if not lists:
        print(
            "No list IDs configured. Set CLICKUP_SPRINT_LIST_ID and/or CLICKUP_BACKLOG_LIST_IDS.",
            file=sys.stderr,
        )
        sys.exit(1)

    id_index = build_id_index()
    updated = created = skipped = 0

    for list_id, label in lists:
        tasks = fetch_list_tasks(list_id)
        logging.info(f"Fetched {len(tasks)} tasks from list {list_id} ({label})")

        for cu in tasks:
            cu_id = cu.get("id", "")

            cu_status = STATUS_FROM_CU.get(
                cu.get("status", {}).get("status", "").lower(), ""
            )
            prio_raw  = (cu.get("priority") or {}).get("id")
            cu_prio   = PRIORITY_FROM_CU.get(int(prio_raw) if prio_raw else None, "")
            cu_due    = ""
            if cu.get("due_date"):
                cu_due = datetime.fromtimestamp(int(cu["due_date"]) / 1000).strftime("%Y-%m-%d")

            if cu_id in id_index:
                path = id_index[cu_id]
                try:
                    text = path.read_text()
                    fm, _ = parse_frontmatter(text)
                    changed = False

                    # Don't overwrite locally-finalised statuses
                    if cu_status and fm.get("status") != cu_status \
                            and fm.get("status") not in ("done", "cancelled"):
                        text = update_field(text, "status", cu_status)
                        changed = True

                    if cu_prio and fm.get("priority") != cu_prio:
                        text = update_field(text, "priority", cu_prio)
                        changed = True

                    if cu_due and fm.get("due", "").strip() != cu_due:
                        text = update_field(text, "due", cu_due)
                        changed = True

                    if changed:
                        path.write_text(text)
                        logging.info(f"Updated {path.name} ← {cu_id}")
                        updated += 1
                    else:
                        skipped += 1

                except Exception as e:
                    logging.error(f"Error updating {path}: {e}")

            elif create_missing:
                path = create_task_note(cu, label)
                logging.info(f"Created {path.name} ← {cu_id}")
                created += 1
            else:
                skipped += 1

    msg = f"Pull complete — updated: {updated}, created: {created}, skipped: {skipped}"
    print(msg)
    logging.info(msg)


if __name__ == "__main__":
    main()
