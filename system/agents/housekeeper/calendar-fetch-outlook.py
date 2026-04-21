#!/usr/bin/env python3
"""
Microsoft Outlook/365 calendar fetcher via Microsoft Graph API.
Outputs pipe-delimited records: uid|||title|||start|||end|||allday|||calendar|||rsvp
"""

from __future__ import annotations
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import msal
    import requests
except ImportError:
    print("Missing dependencies. Run: pip3 install msal requests", file=sys.stderr)
    sys.exit(1)

TOKEN_FILE  = Path.home() / ".vault-ms-token.json"
SCOPES      = ["Calendars.Read"]
GRAPH_BASE  = "https://graph.microsoft.com/v1.0"

CLIENT_ID = os.environ.get("MS_CLIENT_ID", "")
TENANT_ID = os.environ.get("MS_TENANT_ID", "common")


def get_app() -> msal.PublicClientApplication:
    return msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    )


def load_token() -> dict | None:
    if TOKEN_FILE.exists():
        try:
            return json.loads(TOKEN_FILE.read_text())
        except Exception:
            return None
    return None


def save_token(token: dict):
    TOKEN_FILE.write_text(json.dumps(token))
    TOKEN_FILE.chmod(0o600)


def acquire_token() -> str:
    if not CLIENT_ID:
        print("MS_CLIENT_ID not set. Run the installer to configure Outlook.", file=sys.stderr)
        sys.exit(1)

    app = get_app()

    # Try cached token first
    cached = load_token()
    if cached:
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(SCOPES, account=accounts[0])
            if result and "access_token" in result:
                return result["access_token"]

    # Device code flow — works headlessly and in terminals
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        print(f"Could not initiate device flow: {flow}", file=sys.stderr)
        sys.exit(1)

    print(f"\n  Open: {flow['verification_uri']}", file=sys.stderr)
    print(f"  Code: {flow['user_code']}\n", file=sys.stderr)

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        print(f"Auth failed: {result.get('error_description', result)}", file=sys.stderr)
        sys.exit(1)

    save_token(result)
    return result["access_token"]


def rsvp_status(event: dict) -> str:
    for att in event.get("attendees", []):
        if att.get("type") == "required" and att.get("emailAddress", {}).get("address", "").lower() in (
            os.environ.get("MY_EMAIL", "").lower(),
        ):
            status = att.get("status", {}).get("response", "").lower()
            return {"accepted": "accepted", "declined": "declined", "tentativelyaccepted": "tentative"}.get(status, "pending")
    return "no-attendees"


def fetch_events(token: str) -> list[dict]:
    now   = datetime.now(timezone.utc)
    start = (now - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
    end   = (now + timedelta(days=14)).strftime("%Y-%m-%dT23:59:59Z")

    headers = {"Authorization": f"Bearer {token}", "Prefer": 'outlook.timezone="UTC"'}
    params  = {
        "startDateTime": start,
        "endDateTime":   end,
        "$select":       "id,subject,start,end,isAllDay,calendar,attendees,responseStatus,recurrence",
        "$top":          "100",
    }

    r = requests.get(f"{GRAPH_BASE}/me/calendarView", headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("value", [])


def main():
    token  = acquire_token()
    events = fetch_events(token)

    for ev in events:
        uid     = ev.get("id", "")
        title   = ev.get("subject", "(No title)").replace("|||", " ")
        allday  = "true" if ev.get("isAllDay") else "false"
        start   = ev.get("start", {}).get("dateTime", "")[:16].replace("T", " ")
        end     = ev.get("end",   {}).get("dateTime", "")[:16].replace("T", " ")
        cal     = ev.get("calendar", {}).get("name", "Calendar")
        rsvp    = rsvp_status(ev)
        print(f"{uid}|||{title}|||{start}|||{end}|||{allday}|||{cal}|||{rsvp}")


if __name__ == "__main__":
    main()
