#!/bin/bash
# Registers the housekeeping agent's scheduled jobs with launchd.
# Run once after cloning/setting up the vault on a new machine.

set -e

AGENT_DIR="$(cd "$(dirname "$0")" && pwd)"
VAULT="$(cd "$AGENT_DIR/../.." && pwd)"
LAUNCHD="$HOME/Library/LaunchAgents"
PYTHON="/usr/bin/python3"
CLAUDE="${CLAUDE_BIN:-$HOME/.local/bin/claude}"

write_plist() {
  local label="$1"
  local program="$2"
  shift 2
  local args=("$@")

  local file="$LAUNCHD/$label.plist"

  cat > "$file" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$label</string>
    <key>ProgramArguments</key>
    <array>
        <string>$program</string>
$(for a in "${args[@]}"; do echo "        <string>$a</string>"; done)
    </array>
    <key>StartCalendarInterval</key>
    <array>
        $(for day in 1 2 3 4 5; do
            echo "<dict><key>Weekday</key><integer>$day</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>"
            echo "<dict><key>Weekday</key><integer>$day</integer><key>Hour</key><integer>18</integer><key>Minute</key><integer>0</integer></dict>"
          done)
    </array>
    <key>StandardOutPath</key>
    <string>$AGENT_DIR/${label##*.}.log</string>
    <key>StandardErrorPath</key>
    <string>$AGENT_DIR/${label##*.}.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/$USER/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>HOME</key>
        <string>$HOME</string>
    </dict>
</dict>
</plist>
EOF
  launchctl unload "$file" 2>/dev/null || true
  launchctl load "$file"
  echo "✓ $label registered"
}

write_plist "com.oz.calendar-sync" "$PYTHON" "$AGENT_DIR/calendar-sync.py"
write_plist "com.oz.meetily-sync"  "$PYTHON" "$AGENT_DIR/meetily-export.py"

# Daily assimilate runs only at 18:00 — write separately
ASSIMILATE="$LAUNCHD/com.oz.daily-assimilate.plist"
cat > "$ASSIMILATE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.oz.daily-assimilate</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$AGENT_DIR/daily-assimilate.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        $(for day in 1 2 3 4 5; do
            echo "<dict><key>Weekday</key><integer>$day</integer><key>Hour</key><integer>18</integer><key>Minute</key><integer>0</integer></dict>"
          done)
    </array>
    <key>StandardOutPath</key>
    <string>$AGENT_DIR/daily-assimilate.log</string>
    <key>StandardErrorPath</key>
    <string>$AGENT_DIR/daily-assimilate.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/$USER/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>HOME</key>
        <string>$HOME</string>
    </dict>
</dict>
</plist>
EOF
launchctl unload "$ASSIMILATE" 2>/dev/null || true
launchctl load "$ASSIMILATE"
echo "✓ com.oz.daily-assimilate registered"

echo ""
echo "All housekeeping jobs registered. Run 'launchctl list | grep com.oz' to verify."
