#!/usr/bin/env bash
# One-time setup: install rclone and configure the 'gdrive' Google Drive remote.
# Run this once on any machine that will sync ai-context/ to Google Drive.

set -euo pipefail

echo "=== H4YF Google Drive Sync Setup ==="
echo ""

# Install rclone if missing
if ! command -v rclone &>/dev/null; then
  echo "Installing rclone..."
  curl -fsSL https://rclone.org/install.sh | sudo bash
  echo ""
fi

echo "rclone version: $(rclone version | head -1)"
echo ""

# Check if 'gdrive' remote already exists
if rclone listremotes 2>/dev/null | grep -q "^gdrive:"; then
  echo "Remote 'gdrive' already configured."
  rclone about gdrive: 2>/dev/null || echo "(could not fetch Drive info)"
else
  echo "Configuring Google Drive remote named 'gdrive'..."
  echo "A browser window will open for Google OAuth authentication."
  echo ""
  # Non-interactive: create a Drive remote via rclone config create
  # For headless/server environments, use --auth-no-open-browser and paste the URL
  rclone config create gdrive drive \
    scope "drive" \
    --all
fi

echo ""
echo "Creating remote folder H4YF/ai-context (if it doesn't exist)..."
rclone mkdir "gdrive:H4YF/ai-context" 2>/dev/null || true
echo ""

echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  Initial upload:  ./scripts/drive-sync.sh push"
echo "  Initial pull:    ./scripts/drive-sync.sh pull"
echo "  Check status:    ./scripts/drive-sync.sh status"
