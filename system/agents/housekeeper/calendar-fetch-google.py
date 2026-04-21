#!/usr/bin/env python3
"""
Google Calendar fetcher via Google Calendar API.
Outputs pipe-delimited records: uid|||title|||start|||end|||allday|||calendar|||rsvp
"""

from __future__ import annotations
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("Missing dependencies. Run: pip3 install google-auth google-auth-oauthlib google-api-python-client", file=sys.stderr)
    sys.exit(1)

SCOPES      = ["https://www.googleapis.com/auth/calendar.readonly"]
TOKEN_FILE  = Path.home() / ".vault-google-token.json"
CREDS_FILE  = Path(os.environ.get("GOOGLE_CREDS_FILE",
               str(Path.home() / ".vault-google-credentials.json")))

MY_EMAIL    = os.environ.get("MY_EMAIL", "").lower()


def get_credentials() -> Credentials:
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_FILE.exists():
                print(
                    f"Google credentials file not found at {CREDS_FILE}.\n"
                    "Download it from Google Cloud Console → APIs & Services → Credentials.",
                    file=sys.stderr,
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json())
        TOKEN_FILE.chmod(0o600)

    return creds


def rsvp_status(event: dict) -> str:
    attendees = event.get("attendees", [])
    if not attendees:
        return "no-attendees"
    for att in attendees:
        if att.get("self") or att.get("email", "").lower() == MY_EMAIL:
            status = att.get("responseStatus", "needsAction")
            return {
                "accepted":    "accepted",
                "declined":    "declined",
                "tentative":   "tentative",
                "needsAction": "pending",
            }.get(status, "pending")
    return "pending"


def fetch_events(service) -> list[dict]:
    now   = datetime.now(timezone.utc)
    start = (now - timedelta(days=1)).isoformat()
    end   = (now + timedelta(days=14)).isoformat()

    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy="startTime",
            maxResults=100,
        )
        .execute()
    )
    return result.get("items", [])


def main():
    creds   = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    events  = fetch_events(service)

    for ev in events:
        if ev.get("status") == "cancelled":
            continue

        uid    = ev.get("id", "")
        title  = ev.get("summary", "(No title)").replace("|||", " ")
        allday = "true" if "date" in ev.get("start", {}) else "false"

        if allday == "true":
            start = ev["start"]["date"] + " 00:00"
            end   = ev["end"]["date"]   + " 00:00"
        else:
            start = ev["start"].get("dateTime", "")[:16].replace("T", " ")
            end   = ev["end"].get("dateTime",   "")[:16].replace("T", " ")

        cal  = ev.get("organizer", {}).get("displayName", "Google Calendar")
        rsvp = rsvp_status(ev)

        print(f"{uid}|||{title}|||{start}|||{end}|||{allday}|||{cal}|||{rsvp}")


if __name__ == "__main__":
    main()
