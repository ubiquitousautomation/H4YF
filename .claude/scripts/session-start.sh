#!/usr/bin/env bash
# SessionStart hook — delegates to the cross-platform Python runner.
# Thin wrapper kept for backward compatibility with any direct bash invocations.
exec python3 "$(git rev-parse --show-toplevel)/.claude/scripts/hooks.py" session-start
