#!/usr/bin/env bash
# Regenerate CONTEXT.md from the knowledge graph at session start.
# Runs as a Claude Code SessionStart hook.
set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"

if [ -z "$REPO_ROOT" ]; then
    exit 0
fi

KG_SCRIPT="$REPO_ROOT/.claude/scripts/kg.py"
CONTEXT_FILE="$REPO_ROOT/CONTEXT.md"

if [ -f "$KG_SCRIPT" ]; then
    python3 "$KG_SCRIPT" summary > "$CONTEXT_FILE" 2>/dev/null && \
        echo "[kg] CONTEXT.md regenerated from knowledge graph" || \
        echo "[kg] Warning: failed to regenerate CONTEXT.md"
fi
