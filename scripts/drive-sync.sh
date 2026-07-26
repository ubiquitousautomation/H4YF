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
  # rclone copy: never deletes remote files — safe when Gemini may have added Drive-only files
  log "PUSH  $LOCAL_DIR -> $REMOTE_DIR"
  rclone copy "$LOCAL_DIR" "$REMOTE_DIR" --progress --log-file="$LOG_FILE" --log-level INFO
  log "PUSH  done"
}

cmd_fullsync() {
  # rclone sync: makes Drive an exact mirror of local (DELETES remote extras). Use deliberately.
  log "FULLSYNC $LOCAL_DIR -> $REMOTE_DIR (destructive)"
  rclone sync "$LOCAL_DIR" "$REMOTE_DIR" --progress --log-file="$LOG_FILE" --log-level INFO
  log "FULLSYNC done"
}

cmd_pull() {
  # rclone copy: never deletes local files — safe when Claude has added local-only files not yet pushed
  log "PULL  $REMOTE_DIR -> $LOCAL_DIR"
  rclone copy "$REMOTE_DIR" "$LOCAL_DIR" --progress --log-file="$LOG_FILE" --log-level INFO
  log "PULL  done"
}

cmd_bisync() {
  log "BISYNC $LOCAL_DIR <-> $REMOTE_DIR"
  # --first-run seeds the tracking DB on first invocation; subsequent runs detect it automatically
  FIRST_RUN_FLAG=""
  BISYNC_DB="${HOME}/.cache/rclone/bisync"
  if [[ ! -d "$BISYNC_DB" ]] || [[ -z "$(ls -A "$BISYNC_DB" 2>/dev/null)" ]]; then
    FIRST_RUN_FLAG="--first-run"
    log "First bisync run detected — seeding tracking database"
  fi
  rclone bisync "$LOCAL_DIR" "$REMOTE_DIR" \
    --resilient --recover $FIRST_RUN_FLAG \
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
  push)      cmd_push ;;
  pull)      cmd_pull ;;
  bisync)    cmd_bisync ;;
  fullsync)  cmd_fullsync ;;
  status)    cmd_status ;;
  *)
    echo "Usage: $0 [push|pull|bisync|fullsync|status]"
    echo "  push      Copy local ai-context/ to Drive (safe — never deletes remote files)"
    echo "  pull      Copy Drive to local ai-context/ (safe — never deletes local files)"
    echo "  bisync    Two-way sync (auto-detects first run)"
    echo "  fullsync  Make Drive an exact mirror of local (DELETES remote extras)"
    echo "  status    Show diff between local and remote"
    exit 1
    ;;
esac
