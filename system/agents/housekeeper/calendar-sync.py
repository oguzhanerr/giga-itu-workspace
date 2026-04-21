#!/usr/bin/env python3
"""
Syncs Apple Calendar with Obsidian vault via EventKit (calendar-fetch.swift).
Creates meeting stubs in meetings/ for upcoming accepted events (14 days).
Skips declined and unresponded invites.
"""

from __future__ import annotations
import os
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

VAULT        = Path(os.environ["VAULT_DIR"]) if "VAULT_DIR" in os.environ else Path(__file__).parents[3]
MEETINGS_DIR = VAULT / "meetings"
SWIFT_SCRIPT = Path(__file__).parent / "calendar-fetch.swift"

# Events to skip regardless of RSVP (personal blocks, not meetings)
SKIP_TITLES  = {"lunch", "breakfast", "dinner"}


def fetch_events() -> str:
    r = subprocess.run(
        ["swift", str(SWIFT_SCRIPT)],
        capture_output=True, text=True, timeout=30,
    )
    return r.stdout.strip()


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9 ]", "", text.lower())
    return re.sub(r"\s+", "-", text.strip())[:60].rstrip("-")


def parse_events(raw: str) -> list[dict]:
    events = []
    for line in raw.splitlines():
        parts = line.split("|||")
        if len(parts) < 7:
            continue
        uid, title, start_str, end_str, all_day, cal, rsvp = parts[:7]
        try:
            start = datetime.fromisoformat(start_str.strip())
            end   = datetime.fromisoformat(end_str.strip())
        except ValueError:
            continue
        events.append({
            "uid":     uid.strip(),
            "title":   title.strip(),
            "start":   start,
            "end":     end,
            "all_day": all_day.strip() == "true",
            "calendar": cal.strip(),
            "rsvp":    rsvp.strip(),
        })
    return events


def create_stub(ev: dict) -> Optional[Path]:
    date_str     = ev["start"].strftime("%Y-%m-%d")
    time_str     = ev["start"].strftime("%H:%M") if not ev["all_day"] else "All day"
    end_time_str = ev["end"].strftime("%H:%M")   if not ev["all_day"] else ""
    title        = ev["title"]

    safe_title = re.sub(r'[\/\\:*?"<>|]', "-", title)
    path = MEETINGS_DIR / f"{date_str} {safe_title}.md"
    if path.exists():
        return None

    duration = ""
    if not ev["all_day"]:
        mins = int((ev["end"] - ev["start"]).total_seconds() / 60)
        duration = (f" ({mins} min)"            if mins < 60
                    else f" ({mins // 60}h{mins % 60:02d}m)" if mins % 60
                    else f" ({mins // 60}h)")

    rsvp_display = {"accepted": "✓ Accepted", "no-attendees": "—"}.get(
        ev["rsvp"], ev["rsvp"].title()
    )

    lines = [
        f"**Date:** {date_str}  ",
        f"**Time:** {time_str}{'–' + end_time_str if end_time_str else ''}{duration}  ",
        f"**Calendar:** {ev['calendar']}  ",
        f"**RSVP:** {rsvp_display}  ",
        "",
        "## Notes",
        "",
        "## Action Items",
        "",
    ]
    path.write_text("\n".join(lines))
    return path


def main() -> None:
    raw    = fetch_events()
    events = parse_events(raw)
    now    = datetime.now()

    seen: set = set()
    for ev in events:
        # Skip past events (keep today's even if ended)
        if ev["end"].date() < now.date():
            continue
        # Skip declined / unresponded
        if ev["rsvp"] not in ("accepted", "no-attendees"):
            continue
        # Skip personal blocks
        if ev["title"].strip().lower() in SKIP_TITLES:
            continue
        # Deduplicate
        key = (ev["title"], ev["start"].strftime("%Y-%m-%d"))
        if key in seen:
            continue
        seen.add(key)

        path = create_stub(ev)
        if path:
            print(f"Stub: {path.name}")


if __name__ == "__main__":
    main()
