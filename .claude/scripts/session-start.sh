#!/usr/bin/env bash
# SessionStart hook — regenerates CONTEXT.md from the knowledge graph and
# exports a unique KG_SESSION_ID so nodes created this session are traceable.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"

if [[ -z "$REPO_ROOT" ]]; then
    echo "[kg] Not inside a git repo — skipping"
    exit 0
fi

KG_SCRIPT="$REPO_ROOT/.claude/scripts/kg.py"
CONTEXT_FILE="$REPO_ROOT/CONTEXT.md"
GRAPH_FILE="$REPO_ROOT/.claude/knowledge-graph.json"

if [[ ! -f "$KG_SCRIPT" || ! -f "$GRAPH_FILE" ]]; then
    exit 0
fi

# Validate graph integrity before injecting context — surface errors, don't hide them
if ! python3 "$KG_SCRIPT" validate >/dev/null 2>&1; then
    echo "[kg] WARNING: graph failed validation:"
    python3 "$KG_SCRIPT" validate || true
    echo "[kg] CONTEXT.md NOT regenerated — fix the graph first"
    exit 0
fi

# Regenerate CONTEXT.md, showing errors if it fails
if python3 "$KG_SCRIPT" summary > "$CONTEXT_FILE"; then
    NODE_COUNT=$(python3 -c "import json; g=json.load(open('$GRAPH_FILE')); print(len(g['nodes']))" 2>/dev/null || echo "?")
    EDGE_COUNT=$(python3 -c "import json; g=json.load(open('$GRAPH_FILE')); print(len(g['edges']))" 2>/dev/null || echo "?")
    echo "[kg] CONTEXT.md regenerated — ${NODE_COUNT} nodes, ${EDGE_COUNT} edges"
else
    echo "[kg] ERROR: kg.py summary failed — CONTEXT.md may be stale"
fi

# Export a per-session ID so newly created nodes are traceable to this session
SESSION_ID="$(python3 -c 'import uuid; print(str(uuid.uuid4())[:8])')"
if [[ -n "${CLAUDE_ENV_FILE:-}" ]]; then
    echo "KG_SESSION_ID=${SESSION_ID}" >> "$CLAUDE_ENV_FILE"
fi
echo "[kg] Session ID: ${SESSION_ID}"
