#!/usr/bin/env bash
# Stop hook — delegates to the cross-platform Python runner.
# Automatically commits and pushes knowledge-graph.json if it changed this session.
exec python3 "$(git rev-parse --show-toplevel)/.claude/scripts/hooks.py" session-stop
