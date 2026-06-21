#!/usr/bin/env bash
# Sync ai-context/ <-> Google Drive (gdrive:H4YF/ai-context)
# Requires rclone with a remote named 'gdrive'. Run ./scripts/setup-drive.sh first.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_DIR="$REPO_DIR/ai-context"
REMOTE_DIR="gdrive:H4YF/ai-context"
LOG_DIR="$REPO_DIR/.claude"
LOG_FILE="$LOG_DIR/sync.log"

mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

check_rclone() {
  if ! command -v rclone &>/dev/null; then
    echo "ERROR: rclone not installed. Run: ./scripts/setup-drive.sh"
    exit 1
  fi
  if ! rclone listremotes 2>/dev/null | grep -q "^gdrive:"; then
    echo "ERROR: rclone remote 'gdrive' not configured. Run: ./scripts/setup-drive.sh"
    exit 1
  fi
}

cmd_push() {
  log "PUSH  $LOCAL_DIR -> $REMOTE_DIR"
  rclone sync "$LOCAL_DIR" "$REMOTE_DIR" --progress --log-file="$LOG_FILE" --log-level INFO
  log "PUSH  done"
}

cmd_pull() {
  log "PULL  $REMOTE_DIR -> $LOCAL_DIR"
  rclone sync "$REMOTE_DIR" "$LOCAL_DIR" --progress --log-file="$LOG_FILE" --log-level INFO
  log "PULL  done"
}

cmd_bisync() {
  log "BISYNC $LOCAL_DIR <-> $REMOTE_DIR"
  rclone bisync "$LOCAL_DIR" "$REMOTE_DIR" \
    --resilient --recover \
    --progress --log-file="$LOG_FILE" --log-level INFO
  log "BISYNC done"
}

cmd_status() {
  echo "Local:  $LOCAL_DIR"
  echo "Remote: $REMOTE_DIR"
  rclone check "$LOCAL_DIR" "$REMOTE_DIR" 2>&1 | tail -5 || true
}

MODE="${1:-push}"
check_rclone
case "$MODE" in
  push)    cmd_push ;;
  pull)    cmd_pull ;;
  bisync)  cmd_bisync ;;
  status)  cmd_status ;;
  *)
    echo "Usage: $0 [push|pull|bisync|status]"
    echo "  push    Upload ai-context/ to Google Drive (default)"
    echo "  pull    Download from Google Drive to ai-context/"
    echo "  bisync  Two-way sync (recoverable)"
    echo "  status  Show diff between local and remote"
    exit 1
    ;;
esac
