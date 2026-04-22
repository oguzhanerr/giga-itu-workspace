#!/usr/bin/env python3
"""
Obsidian → ClickUp task sync
Called by fswatch whenever a .md file in tasks/ is created or modified.

Behaviour:
  - No clickup_id in front matter  → create ClickUp task, write ID back to file
  - Has clickup_id                 → update status / priority / due date
  - clickup_list: sprint (default) → current sprint list
  - clickup_list: backlog          → backlog list resolved by project tag
"""

import sys
import os
import re
from pathlib import Path
import json
import time
import logging
import urllib.request
import urllib.error
from datetime import datetime

# ---------------------------------------------------------------------------
# Config — read from env vars or system/config.yaml, never hardcoded
# ---------------------------------------------------------------------------
VAULT     = os.environ.get("VAULT_DIR", str(Path(__file__).parents[4]))
TASKS_DIR = os.path.join(VAULT, "tasks")


def _load_config() -> dict:
    p = Path(VAULT) / "system/config.yaml"
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


SPRINT_LIST_ID = _get("CLICKUP_SPRINT_LIST_ID", "clickup_sprint_list_id")

_bl_json = os.environ.get("CLICKUP_BACKLOG_LIST_IDS")
if _bl_json:
    BACKLOG_LIST_IDS: dict = json.loads(_bl_json)
else:
    BACKLOG_LIST_IDS = {
        k[len("clickup_backlog_"):].replace("_", "-"): v
        for k, v in _cfg.items()
        if k.startswith("clickup_backlog_")
    }

PRIORITY_MAP = {"urgent": 1, "high": 2, "medium": 3, "normal": 3, "low": 4}
STATUS_MAP = {
    "todo":        "to do",
    "in-progress": "in progress",
    "waiting":     "to do",
    "done":        "done",
    "cancelled":   "cancelled",
}
ACRONYMS = {"mst", "itu", "br", "fe", "ux", "mvp", "api", "crm", "pm", "sdk"}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_PATH = os.path.expanduser("~/Library/Logs/obsidian-clickup-sync.log")
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clickup_request(method, path, data=None):
    token = os.environ.get("CLICKUP_TOKEN", "")
    if not token:
        logging.error("CLICKUP_TOKEN not set")
        return None
    url = f"https://api.clickup.com/api/v2{path}"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        logging.error(f"ClickUp {method} {path} → {e.code}: {e.read().decode()}")
        return None


def parse_frontmatter(content):
    """Return (fm_dict, body_str). fm_dict has string values; tags is a list."""
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not match:
        return {}, content

    raw = match.group(1)
    body = match.group(2)
    fm = {}

    # Parse scalar key: value pairs
    for line in raw.split("\n"):
        if re.match(r"^\s{2}-", line):
            continue  # list item handled below
        kv = re.match(r"^(\w[\w_-]*):\s*(.*)", line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip('"')

    # Parse tags list
    tags_block = re.search(r"^tags:\n((?:  - .+\n?)+)", raw, re.MULTILINE)
    if tags_block:
        fm["tags"] = [t.strip().lstrip("- ") for t in tags_block.group(1).strip().splitlines()]
    elif "tags" not in fm:
        fm["tags"] = []

    return fm, body


def slug_to_title(filepath):
    slug = os.path.splitext(os.path.basename(filepath))[0]
    return " ".join(p.upper() if p in ACRONYMS else p.capitalize() for p in slug.split("-"))


def extract_context(body):
    m = re.search(r"## Context\n(.*?)(?=\n##|\Z)", body, re.DOTALL)
    return m.group(1).strip() if m else ""


def due_to_ms(date_str):
    if not date_str or not date_str.strip():
        return None
    try:
        return int(datetime.strptime(date_str.strip(), "%Y-%m-%d").timestamp() * 1000)
    except ValueError:
        return None


def write_clickup_id(filepath, content, clickup_id):
    """Write clickup_id back into front matter."""
    # Replace blank clickup_id: field
    new = re.sub(r"(clickup_id:\s*)$", f"clickup_id: {clickup_id}", content, flags=re.MULTILINE)
    # If still not set, insert after source: line
    if f"clickup_id: {clickup_id}" not in new:
        new = re.sub(r"(source:.*\n)", f"\\1clickup_id: {clickup_id}\n", new)
    with open(filepath, "w") as f:
        f.write(new)


def resolve_list_id(fm):
    target = fm.get("clickup_list", "sprint").strip().lower()
    if target == "none":
        return None
    if target == "backlog":
        tags = fm.get("tags", [])
        for tag in tags:
            if tag in BACKLOG_LIST_IDS:
                return BACKLOG_LIST_IDS[tag]
        logging.warning("clickup_list=backlog but no matching project tag — defaulting to sprint")
    return SPRINT_LIST_ID


# ---------------------------------------------------------------------------
# Main sync logic
# ---------------------------------------------------------------------------

def sync_file(filepath):
    filepath = os.path.abspath(filepath)

    if not filepath.endswith(".md"):
        return
    if not filepath.startswith(TASKS_DIR):
        return

    try:
        with open(filepath, "r") as f:
            content = f.read()
    except Exception as e:
        logging.error(f"Cannot read {filepath}: {e}")
        return

    fm, body = parse_frontmatter(content)
    tags = fm.get("tags", [])

    # Only sync work/development task and idea notes — skip personal
    if "task" not in tags and "idea" not in tags:
        return
    if "personal" in tags:
        return

    # Skip completed/cancelled tasks from being re-created
    if fm.get("status") in ("done", "cancelled") and not fm.get("clickup_id", "").strip():
        return

    description = extract_context(body)
    status      = STATUS_MAP.get(fm.get("status", "todo"), "to do")
    priority    = PRIORITY_MAP.get(fm.get("priority", "medium"), 3)
    due_ms      = due_to_ms(fm.get("due", ""))
    clickup_id  = fm.get("clickup_id", "").strip()

    if clickup_id:
        payload = {"status": status, "priority": priority, "description": description}
        if due_ms:
            payload["due_date"] = due_ms
        result = clickup_request("PUT", f"/task/{clickup_id}", payload)
        if result:
            logging.info(f"Updated {clickup_id} ← {os.path.basename(filepath)}")
        else:
            logging.error(f"Failed to update {clickup_id}")
    else:
        list_id = resolve_list_id(fm)
        if list_id is None:
            logging.info(f"Skipping {os.path.basename(filepath)} (clickup_list: none)")
            return
        payload = {
            "name":        slug_to_title(filepath),
            "description": description,
            "status":      status,
            "priority":    priority,
        }
        if due_ms:
            payload["due_date"] = due_ms
        result = clickup_request("POST", f"/list/{list_id}/task", payload)
        if result and result.get("id"):
            new_id = result["id"]
            write_clickup_id(filepath, content, new_id)
            logging.info(f"Created {new_id} ← {os.path.basename(filepath)} (list {list_id})")
        else:
            logging.error(f"Failed to create task for {os.path.basename(filepath)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    time.sleep(0.5)  # let Obsidian finish writing
    sync_file(sys.argv[1])
