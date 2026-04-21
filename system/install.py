#!/usr/bin/env python3
"""
Vault System Installer
Interactive setup for the full agent stack: Obsidian vault, Claude Code,
ClickUp sync, Meetily, Apple Calendar, MCP, and scheduler.
"""

from __future__ import annotations
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

# ── Helpers ──────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
DIM    = "\033[2m"

def title(text: str):
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}\n")

def ok(text: str):    print(f"  {GREEN}✓{RESET}  {text}")
def warn(text: str):  print(f"  {YELLOW}⚠{RESET}  {text}")
def err(text: str):   print(f"  {RED}✗{RESET}  {text}")
def info(text: str):  print(f"  {DIM}→{RESET}  {text}")
def skip(text: str):  print(f"  {DIM}–{RESET}  {text} {DIM}(skipped){RESET}")

def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        val = input(f"  {BOLD}?{RESET}  {prompt}{hint}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\nInstaller cancelled.")
        sys.exit(0)
    return val if val else default

def confirm(prompt: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    try:
        val = input(f"  {BOLD}?{RESET}  {prompt} [{hint}]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n\nInstaller cancelled.")
        sys.exit(0)
    if not val:
        return default
    return val.startswith("y")

def run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)

# ── State ─────────────────────────────────────────────────────────────────────

OS       = platform.system()  # Darwin / Linux / Windows
IS_MAC   = OS == "Darwin"
IS_LINUX = OS == "Linux"
IS_WIN   = OS == "Windows"

config: dict = {}
results: list[tuple[str, str, str]] = []  # (component, status, note)

VAULT_DIR = Path(__file__).parents[1]

# ── Steps ─────────────────────────────────────────────────────────────────────

def step_welcome():
    print(f"""
{BOLD}╔══════════════════════════════════════════════════════════╗
║           Vault Agent System — Installer                 ║
║                                                          ║
║  Sets up: Obsidian vault · Claude Code · ClickUp sync   ║
║           Meetily · Apple Calendar · MCP · Scheduler    ║
╚══════════════════════════════════════════════════════════╝{RESET}

Platform: {BOLD}{OS}{RESET}
Vault:    {BOLD}{VAULT_DIR}{RESET}

This installer will ask about each component and configure
what's available on your system. You can skip anything.
""")
    if not confirm("Ready to start?"):
        sys.exit(0)


def step_vault():
    title("1 · Obsidian Vault")

    detected = str(VAULT_DIR)
    info(f"Detected vault at: {detected}")

    if confirm("Is this the correct vault path?"):
        config["vault_dir"] = detected
        ok(f"Vault path set to: {detected}")
    else:
        path = ask("Enter the full path to your vault")
        if not Path(path).exists():
            warn("Path doesn't exist — setting it anyway, but check before proceeding.")
        config["vault_dir"] = path
        ok(f"Vault path set to: {path}")

    results.append(("Obsidian vault", "✓", config["vault_dir"]))


def step_claude():
    title("2 · Claude Code CLI")

    detected = shutil.which("claude") or str(Path.home() / ".local/bin/claude")
    exists   = Path(detected).exists()

    if exists:
        ok(f"Found Claude CLI at: {detected}")
        config["claude_bin"] = detected
    else:
        warn("Claude CLI not found in PATH.")
        if confirm("Do you have Claude Code installed?"):
            path = ask("Enter path to claude binary", detected)
            config["claude_bin"] = path
            if Path(path).exists():
                ok(f"Claude CLI set to: {path}")
            else:
                warn(f"Binary not found at {path} — set CLAUDE_BIN env var manually.")
        else:
            info("Install Claude Code from: https://claude.ai/code")
            config["claude_bin"] = detected
            results.append(("Claude Code CLI", "⚠", "Not installed — install from claude.ai/code"))
            return

    # Verify version
    r = run([config["claude_bin"], "--version"])
    version = r.stdout.strip() or r.stderr.strip()
    if version:
        info(f"Version: {version}")

    results.append(("Claude Code CLI", "✓", config["claude_bin"]))


def step_clickup():
    title("3 · ClickUp Sync")

    if not confirm("Do you use ClickUp?"):
        skip("ClickUp")
        config["clickup_enabled"] = False
        results.append(("ClickUp sync", "–", "Skipped"))
        return

    config["clickup_enabled"] = True

    token = ask("ClickUp API token (pk_...)")
    if not token.startswith("pk_"):
        warn("Token doesn't look right — should start with pk_")
    config["clickup_token"] = token

    sprint_list = ask("Sprint list ID (find in ClickUp URL when viewing the list)")
    config["clickup_sprint_list_id"] = sprint_list

    backlog_list = ask("Backlog list ID (leave blank to skip)", "")
    if backlog_list:
        config["clickup_backlog_list_id"] = backlog_list

    # Check fswatch (macOS/Linux)
    if not IS_WIN:
        fswatch = shutil.which("fswatch")
        if fswatch:
            ok(f"fswatch found at: {fswatch}")
            config["fswatch_bin"] = fswatch
        else:
            warn("fswatch not found.")
            if IS_MAC:
                info("Install with: brew install fswatch")
            elif IS_LINUX:
                info("Install with: apt install fswatch  or  dnf install fswatch")
            results.append(("ClickUp sync / fswatch", "⚠", "Install fswatch then re-run"))
            return
    else:
        info("Windows: fswatch not supported. ClickUp sync requires manual trigger or WSL.")
        results.append(("ClickUp sync", "⚠", "Not supported on Windows without WSL"))
        return

    results.append(("ClickUp sync", "✓", f"Token set · Sprint list: {sprint_list}"))


def step_meetily():
    title("4 · Meetily Export")

    if not confirm("Do you use Meetily for meeting recordings?"):
        skip("Meetily")
        results.append(("Meetily export", "–", "Skipped"))
        config["meetily_enabled"] = False
        return

    config["meetily_enabled"] = True

    # OS-aware default path
    if IS_MAC:
        default_db = str(Path.home() / "Library/Application Support/com.meetily.ai/meeting_minutes.sqlite")
    elif IS_WIN:
        default_db = str(Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "com.meetily.ai/meeting_minutes.sqlite")
    else:
        xdg = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        default_db = str(xdg / "com.meetily.ai/meeting_minutes.sqlite")

    if Path(default_db).exists():
        ok("Meetily database found at default path.")
        config["meetily_db"] = default_db
    else:
        warn("Meetily database not found at default path.")
        if confirm("Is Meetily installed?"):
            path = ask("Path to Meetily SQLite database", default_db)
            config["meetily_db"] = path
            if not Path(path).exists():
                warn("Database not found — make sure Meetily has been run at least once.")
        else:
            info("Install Meetily from: https://meetily.ai")
            config["meetily_db"] = default_db
            results.append(("Meetily export", "⚠", "Install Meetily and re-run"))
            return

    results.append(("Meetily export", "✓", config["meetily_db"]))


def step_calendar():
    title("5 · Calendar Sync")

    if not confirm("Do you want to sync your calendar to the vault?"):
        skip("Calendar sync")
        config["calendar_enabled"] = False
        results.append(("Calendar sync", "–", "Skipped"))
        return

    config["calendar_enabled"] = True

    # Ask which provider
    print()
    print(f"  Which calendar do you use?")
    options = []
    if IS_MAC:
        options.append(("apple",   "Apple Calendar (macOS only)"))
    options.append(("outlook", "Microsoft Outlook / 365"))
    options.append(("google",  "Google Calendar"))

    for i, (key, label) in enumerate(options, 1):
        print(f"  {DIM}{i}{RESET}  {label}")
    print()

    while True:
        choice = ask(f"Enter number [1–{len(options)}]")
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            provider = options[int(choice) - 1][0]
            break
        warn("Invalid choice — try again.")

    config["calendar_provider"] = provider
    ok(f"Calendar provider: {provider}")

    if provider == "apple":
        _setup_calendar_apple()
    elif provider == "outlook":
        _setup_calendar_outlook()
    elif provider == "google":
        _setup_calendar_google()


def _setup_calendar_apple():
    swift = shutil.which("swift")
    if swift:
        ok(f"Swift found at: {swift}")
    else:
        err("Swift not found — required for EventKit access.")
        info("Install Xcode Command Line Tools: xcode-select --install")
        results.append(("Calendar sync", "⚠", "Install Xcode Command Line Tools"))
        return
    info("Calendar access requires permission — you may see a system prompt on first run.")
    results.append(("Calendar sync", "✓", "Apple Calendar · Swift found"))


def _setup_calendar_outlook():
    print()
    info("Outlook calendar sync uses the Microsoft Graph API.")
    info("You need a free Azure app registration. Steps:")
    info("  1. Go to https://portal.azure.com → Azure Active Directory → App registrations")
    info("  2. New registration → any name → Accounts in any org + personal")
    info("  3. Add permission: Microsoft Graph → Delegated → Calendars.Read")
    info("  4. Copy the Application (client) ID")
    print()

    client_id = ask("Azure Application (client) ID")
    tenant_id = ask("Tenant ID (leave blank for personal/multi-tenant accounts)", "common")

    config["ms_client_id"] = client_id
    config["ms_tenant_id"] = tenant_id or "common"

    my_email = ask("Your Outlook email address (used for RSVP detection)")
    config["my_email"] = my_email

    # Verify msal is installed
    try:
        import msal  # noqa
        ok("msal library found.")
    except ImportError:
        warn("msal not installed — will be installed in the dependencies step.")

    results.append(("Calendar sync", "✓", f"Outlook · client_id set · first run will open browser for auth"))


def _setup_calendar_google():
    print()
    info("Google Calendar sync uses the Google Calendar API.")
    info("You need a free Google Cloud credentials file. Steps:")
    info("  1. Go to https://console.cloud.google.com → APIs & Services → Credentials")
    info("  2. Create OAuth 2.0 Client ID → Desktop app")
    info("  3. Download the JSON credentials file")
    print()

    creds_path = ask(
        "Path to downloaded credentials JSON file",
        str(Path.home() / ".vault-google-credentials.json"),
    )

    if Path(creds_path).exists():
        # Copy to standard location if not already there
        target = Path.home() / ".vault-google-credentials.json"
        if Path(creds_path) != target:
            import shutil as _shutil
            _shutil.copy(creds_path, target)
            target.chmod(0o600)
            ok(f"Credentials copied to: {target}")
        config["google_creds_file"] = str(target)
    else:
        warn(f"File not found at {creds_path} — set GOOGLE_CREDS_FILE env var before first run.")
        config["google_creds_file"] = creds_path

    my_email = ask("Your Google account email (used for RSVP detection)")
    config["my_email"] = my_email

    try:
        from googleapiclient.discovery import build  # noqa
        ok("Google API libraries found.")
    except ImportError:
        warn("Google libraries not installed — will be installed in the dependencies step.")

    results.append(("Calendar sync", "✓", f"Google Calendar · first run will open browser for auth"))


def step_mcp():
    title("6 · Claude Desktop MCP (Filesystem)")

    if IS_WIN:
        config_path = Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json"
    else:
        config_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"

    if not config_path.exists():
        warn(f"Claude desktop config not found at: {config_path}")
        info("Install the Claude desktop app from: https://claude.ai/download")
        results.append(("Claude desktop MCP", "⚠", "Claude desktop app not installed"))
        return

    if not confirm("Configure Claude desktop app to access the vault via MCP?"):
        skip("Claude desktop MCP")
        results.append(("Claude desktop MCP", "–", "Skipped"))
        return

    # Check node / npx
    npx = shutil.which("npx")
    if not npx:
        warn("npx not found — required for the filesystem MCP server.")
        if IS_MAC:
            info("Install Node.js with: brew install node")
        elif IS_LINUX:
            info("Install Node.js with: apt install nodejs npm")
        else:
            info("Install Node.js from: https://nodejs.org")
        results.append(("Claude desktop MCP", "⚠", "Install Node.js and re-run"))
        return

    ok(f"npx found at: {npx}")

    # Read and patch config
    try:
        with open(config_path) as f:
            desktop_config = json.load(f)
    except Exception as e:
        err(f"Could not read config: {e}")
        results.append(("Claude desktop MCP", "✗", str(e)))
        return

    mcp_servers = desktop_config.setdefault("mcpServers", {})
    vault_path  = config.get("vault_dir", str(VAULT_DIR))

    mcp_servers["obsidian-vault"] = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", vault_path]
    }

    with open(config_path, "w") as f:
        json.dump(desktop_config, f, indent=2)

    ok(f"MCP server configured → restart Claude desktop app to apply.")
    info(f"Config: {config_path}")
    results.append(("Claude desktop MCP", "✓", "Restart Claude desktop app to apply"))


def step_scheduler():
    title("7 · Scheduler")

    agent_dir = VAULT_DIR / "system/agents/housekeeper"

    if IS_MAC:
        _setup_launchd(agent_dir)
    elif IS_LINUX:
        _setup_systemd(agent_dir)
    else:
        _setup_windows(agent_dir)


def _setup_launchd(agent_dir: Path):
    if not confirm("Register scheduled jobs with launchd (macOS)?"):
        skip("launchd scheduler")
        results.append(("Scheduler", "–", "Skipped"))
        return

    prefix = ask("launchd label prefix", "com.yourname")
    config["launchd_prefix"] = prefix

    launchd_dir = Path.home() / "Library/LaunchAgents"
    vault_path  = config.get("vault_dir", str(VAULT_DIR))
    python      = shutil.which("python3") or "/usr/bin/python3"
    claude      = config.get("claude_bin", str(Path.home() / ".local/bin/claude"))

    jobs = []

    if config.get("calendar_enabled"):
        jobs.append((f"{prefix}.calendar-sync", python,
                     [str(agent_dir / "calendar-sync.py")],
                     str(agent_dir / "calendar-sync.log"),
                     [8, 18]))

    if config.get("meetily_enabled"):
        jobs.append((f"{prefix}.meetily-sync", python,
                     [str(agent_dir / "meetily-export.py")],
                     str(agent_dir / "meetily-export.log"),
                     [8, 18]))

    # Daily assimilate always
    jobs.append((f"{prefix}.daily-assimilate", "/bin/bash",
                 [str(agent_dir / "daily-assimilate.sh")],
                 str(agent_dir / "daily-assimilate.log"),
                 [18]))

    env_vars = {
        "PATH": f"{Path.home()}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin",
        "HOME": str(Path.home()),
        "VAULT_DIR": vault_path,
    }
    if config.get("meetily_db"):
        env_vars["MEETILY_DB"] = config["meetily_db"]
    if config.get("claude_bin"):
        env_vars["CLAUDE_BIN"] = config["claude_bin"]
    if config.get("calendar_provider"):
        env_vars["CALENDAR_PROVIDER"] = config["calendar_provider"]
    if config.get("my_email"):
        env_vars["MY_EMAIL"] = config["my_email"]
    if config.get("ms_client_id"):
        env_vars["MS_CLIENT_ID"] = config["ms_client_id"]
        env_vars["MS_TENANT_ID"] = config.get("ms_tenant_id", "common")
    if config.get("google_creds_file"):
        env_vars["GOOGLE_CREDS_FILE"] = config["google_creds_file"]

    for label, program, args, log, hours in jobs:
        intervals = []
        for h in hours:
            for day in range(1, 6):
                intervals.append(f"""        <dict><key>Weekday</key><integer>{day}</integer><key>Hour</key><integer>{h}</integer><key>Minute</key><integer>0</integer></dict>""")

        args_xml = "\n".join(f"        <string>{a}</string>" for a in args)
        env_xml  = "\n".join(
            f"        <key>{k}</key>\n        <string>{v}</string>"
            for k, v in env_vars.items()
        )

        plist = dedent(f"""\
            <?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
              "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
            <plist version="1.0">
            <dict>
                <key>Label</key>
                <string>{label}</string>
                <key>ProgramArguments</key>
                <array>
                    <string>{program}</string>
            {args_xml}
                </array>
                <key>StartCalendarInterval</key>
                <array>
            {chr(10).join(intervals)}
                </array>
                <key>StandardOutPath</key>
                <string>{log}</string>
                <key>StandardErrorPath</key>
                <string>{log}</string>
                <key>EnvironmentVariables</key>
                <dict>
            {env_xml}
                </dict>
            </dict>
            </plist>
        """)

        plist_path = launchd_dir / f"{label}.plist"
        plist_path.write_text(plist)

        # Unload existing, load new
        run(["launchctl", "unload", str(plist_path)])
        r = run(["launchctl", "load", str(plist_path)])
        if r.returncode == 0:
            ok(f"Registered: {label}")
        else:
            warn(f"Could not load {label}: {r.stderr.strip()}")

    results.append(("Scheduler (launchd)", "✓", f"{len(jobs)} jobs registered with prefix {prefix}"))


def _setup_systemd(agent_dir: Path):
    info("Linux systemd setup — generating unit files.")
    vault_path = config.get("vault_dir", str(VAULT_DIR))
    python     = shutil.which("python3") or "python3"

    unit_dir = Path.home() / ".config/systemd/user"
    unit_dir.mkdir(parents=True, exist_ok=True)

    jobs = []
    if config.get("calendar_enabled"):
        warn("Calendar sync is not available on Linux (Apple Calendar / EventKit is macOS-only).")
    if config.get("meetily_enabled"):
        warn("Meetily export is not available on Linux (Meetily is a macOS app).")

    # Daily assimilate
    jobs.append(("vault-assimilate", str(agent_dir / "daily-assimilate.sh"), "18:00"))

    for name, script, time_val in jobs:
        service = dedent(f"""\
            [Unit]
            Description=Vault {name}

            [Service]
            Type=oneshot
            ExecStart=/bin/bash {script}
            Environment=VAULT_DIR={vault_path}
            Environment=HOME={Path.home()}
        """)
        timer = dedent(f"""\
            [Unit]
            Description=Run vault-{name} on weekdays at {time_val}

            [Timer]
            OnCalendar=Mon-Fri {time_val}
            Persistent=true

            [Install]
            WantedBy=timers.target
        """)
        (unit_dir / f"{name}.service").write_text(service)
        (unit_dir / f"{name}.timer").write_text(timer)
        info(f"Written: {unit_dir}/{name}.service + .timer")

    print()
    info("To enable, run:")
    for name, _, _ in jobs:
        info(f"  systemctl --user enable --now {name}.timer")

    results.append(("Scheduler (systemd)", "✓", f"Unit files written to {unit_dir} — enable manually"))


def _setup_windows(agent_dir: Path):
    info("Windows Task Scheduler — manual setup required.")
    print()
    info("To schedule the daily assimilate on Windows:")
    info("  1. Open Task Scheduler")
    info(f"  2. Create a task that runs: bash {agent_dir / 'daily-assimilate.sh'}")
    info("  3. Set trigger: Mon–Fri at 18:00")
    info(f"  4. Set environment variable: VAULT_DIR={config.get('vault_dir', VAULT_DIR)}")
    print()
    info("Calendar sync and Meetily export are not available on Windows.")
    results.append(("Scheduler (Windows)", "⚠", "Manual Task Scheduler setup required"))


def step_dependencies():
    title("8 · Python Dependencies")

    req_file = VAULT_DIR / "system/requirements.txt"
    if not req_file.exists():
        skip("requirements.txt not found")
        results.append(("Python dependencies", "–", "requirements.txt not found"))
        return

    pip = shutil.which("pip3") or shutil.which("pip")
    if not pip:
        warn("pip not found — install dependencies manually:")
        info(f"  pip3 install -r {req_file}")
        results.append(("Python dependencies", "⚠", "pip not found — install manually"))
        return

    if not confirm("Install Python dependencies from requirements.txt?", default=True):
        skip("Python dependencies")
        results.append(("Python dependencies", "–", "Skipped"))
        return

    r = run([pip, "install", "-r", str(req_file)])
    if r.returncode == 0:
        ok("Dependencies installed.")
        results.append(("Python dependencies", "✓", str(req_file)))
    else:
        err(f"pip install failed: {r.stderr.strip()}")
        results.append(("Python dependencies", "✗", r.stderr.strip()[:80]))


def step_config():
    title("9 · Writing config.yaml")

    config_path = VAULT_DIR / "system/config.yaml"

    lines = [
        "# Generated by install.py — personal config, do not share.",
        "",
        f"vault_dir: {config.get('vault_dir', str(VAULT_DIR))}",
        f"claude_bin: {config.get('claude_bin', '~/.local/bin/claude')}",
    ]

    if config.get("launchd_prefix"):
        lines.append(f"launchd_prefix: {config['launchd_prefix']}")

    if config.get("clickup_enabled"):
        lines += [
            "",
            f"clickup_token: {config.get('clickup_token', '')}",
            f"clickup_sprint_list_id: {config.get('clickup_sprint_list_id', '')}",
        ]
        if config.get("clickup_backlog_list_id"):
            lines.append(f"clickup_backlog_list_id: {config['clickup_backlog_list_id']}")

    if config.get("meetily_db"):
        lines += [
            "",
            f"meetily_db: {config['meetily_db']}",
        ]

    if config.get("calendar_provider"):
        lines += [
            "",
            f"calendar_provider: {config['calendar_provider']}",
        ]
        if config.get("my_email"):
            lines.append(f"my_email: {config['my_email']}")
        if config.get("ms_client_id"):
            lines.append(f"ms_client_id: {config['ms_client_id']}")
            lines.append(f"ms_tenant_id: {config.get('ms_tenant_id', 'common')}")
        if config.get("google_creds_file"):
            lines.append(f"google_creds_file: {config['google_creds_file']}")

    config_path.write_text("\n".join(lines) + "\n")
    ok(f"Written: {config_path}")
    results.append(("Config file", "✓", str(config_path)))


def step_summary():
    title("Setup Summary")

    max_w = max(len(c) for c, _, _ in results)
    for component, status, note in results:
        color = GREEN if status == "✓" else (YELLOW if status == "⚠" else DIM)
        print(f"  {color}{status}{RESET}  {component:<{max_w}}  {DIM}{note}{RESET}")

    print()
    warnings = [r for r in results if r[1] == "⚠"]
    errors   = [r for r in results if r[1] == "✗"]

    if errors:
        err(f"{len(errors)} component(s) failed — check output above.")
    if warnings:
        warn(f"{len(warnings)} component(s) need attention — see notes above.")
    if not errors and not warnings:
        ok("All components set up successfully.")

    print(f"\n  {DIM}Run this installer again any time to update your config.{RESET}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    step_welcome()
    step_vault()
    step_claude()
    step_clickup()
    step_meetily()
    step_calendar()
    step_mcp()
    step_scheduler()
    step_dependencies()
    step_config()
    step_summary()


if __name__ == "__main__":
    main()
