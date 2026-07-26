#!/usr/bin/env bash
# One-time setup: install rclone and configure the 'gdrive' Google Drive remote.
#
# WINDOWS USERS: This is a bash script — run it in Git Bash or WSL, not PowerShell.
#   Git Bash:  open Git Bash terminal, cd to repo root, then: bash ./scripts/setup-drive.sh
#   WSL:       open WSL terminal, cd to repo root, then: bash ./scripts/setup-drive.sh
#
# REMOTE/HEADLESS (Claude Code cloud container): use the TOKEN flow below.
#   The container has no browser, so OAuth must be completed on your local machine first.
#   Step 1 — on your LOCAL machine (Windows/Mac/Linux with a browser):
#     Install rclone: https://rclone.org/install/
#     Run: rclone authorize "drive" --client-id="" --client-secret=""
#     A browser opens → sign in → copy the JSON token that prints in the terminal.
#   Step 2 — back in the Claude Code terminal (Linux container):
#     Run: rclone config create gdrive drive scope drive token '<paste-json-here>'
#   Then continue with: ./scripts/drive-sync.sh push

set -euo pipefail

echo "=== H4YF Google Drive Sync Setup ==="
echo ""

# Install rclone if missing (Linux only; Windows users install manually)
if ! command -v rclone &>/dev/null; then
  if [[ "$(uname)" == "Linux" ]]; then
    echo "Installing rclone..."
    curl -fsSL https://rclone.org/install.sh | sudo bash
    echo ""
  else
    echo "ERROR: rclone not found. Install from https://rclone.org/install/ then re-run."
    exit 1
  fi
fi

echo "rclone $(rclone version | head -1)"
echo ""

# Check if 'gdrive' remote already exists
if rclone listremotes 2>/dev/null | grep -q "^gdrive:"; then
  echo "Remote 'gdrive' is already configured."
  rclone about gdrive: 2>/dev/null || echo "(could not fetch Drive quota info)"
else
  echo "Configuring Google Drive remote named 'gdrive'..."
  echo ""

  # Detect headless environment (no display available)
  if [[ -z "${DISPLAY:-}" ]] && [[ -z "${WAYLAND_DISPLAY:-}" ]]; then
    echo "No display detected (headless environment)."
    echo ""
    echo "Complete auth on your LOCAL machine first:"
    echo "  1. Install rclone locally: https://rclone.org/install/"
    echo "  2. Run on local machine:   rclone authorize \"drive\""
    echo "  3. Sign in to Google in the browser that opens."
    echo "  4. Copy the JSON token printed in your local terminal."
    echo "  5. Come back here and run:"
    echo "       rclone config create gdrive drive scope drive token '<paste-token-json>'"
    echo ""
    echo "Then re-run this script to create the H4YF folder and verify."
    exit 0
  fi

  # Browser available — interactive flow
  echo "A browser will open for Google OAuth. Sign in as ubiquitousautomation@gmail.com."
  rclone config create gdrive drive scope drive
fi

echo ""
echo "Creating remote folder H4YF/ai-context (if it doesn't exist)..."
rclone mkdir "gdrive:H4YF/ai-context" 2>/dev/null || true

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  Initial upload:  ./scripts/drive-sync.sh push"
echo "  Check status:    ./scripts/drive-sync.sh status"
