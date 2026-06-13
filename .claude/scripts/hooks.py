#!/usr/bin/env python3
"""
Cross-platform Claude Code hook runner — knowledge graph harness.

Called by .claude/settings.json hooks. Uses sys.executable so the same
Python binary that launched this script also runs kg.py (no PATH assumptions).

Usage:
  python3 .claude/scripts/hooks.py session-start
  python3 .claude/scripts/hooks.py session-stop
"""

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


# ── helpers ───────────────────────────────────────────────────────────────────

def find_repo_root() -> Path | None:
    r = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        capture_output=True, text=True,
    )
    return Path(r.stdout.strip()) if r.returncode == 0 else None


def kg(repo_root: Path, *args: str) -> tuple[str, str, int]:
    """Run kg.py with sys.executable — no PATH ambiguity."""
    script = repo_root / '.claude' / 'scripts' / 'kg.py'
    r = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, cwd=repo_root,
    )
    return r.stdout, r.stderr, r.returncode


def graph_is_dirty(repo_root: Path, graph_rel: str) -> bool:
    """True if knowledge-graph.json has any uncommitted change (modified/staged/untracked)."""
    r = subprocess.run(
        ['git', 'status', '--porcelain', graph_rel],
        capture_output=True, text=True, cwd=repo_root,
    )
    return bool(r.stdout.strip())


def git_run(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=repo_root, capture_output=True, text=True)


# ── session-start ─────────────────────────────────────────────────────────────

def session_start(repo_root: Path) -> None:
    graph_path   = repo_root / '.claude' / 'knowledge-graph.json'
    context_file = repo_root / 'CONTEXT.md'

    if not graph_path.exists():
        print('[kg] knowledge-graph.json not found — skipping (run: kg.py init NAME DESC)')
        return

    # Validate before regenerating — surface errors rather than hiding them
    _, stderr, rc = kg(repo_root, 'validate')
    if rc != 0:
        stdout, _, _ = kg(repo_root, 'validate')
        print('[kg] WARNING: graph failed validation — CONTEXT.md not regenerated:')
        print(stdout or stderr)
        return

    # Regenerate CONTEXT.md
    stdout, stderr, rc = kg(repo_root, 'summary')
    if rc != 0:
        print('[kg] ERROR: kg.py summary failed — CONTEXT.md may be stale')
        if stderr:
            print(stderr)
        return

    context_file.write_text(stdout, encoding='utf-8')

    graph = json.loads(graph_path.read_text(encoding='utf-8'))
    n = len(graph.get('nodes', []))
    e = len(graph.get('edges', []))
    active = sum(1 for node in graph.get('nodes', []) if node.get('status', 'active') == 'active')
    print(f'[kg] CONTEXT.md regenerated — {active}/{n} active nodes, {e} edges')

    # Stamp a per-session ID so new nodes are traceable; injected via $CLAUDE_ENV_FILE
    # when running on Claude Code web/remote. Degrades silently on desktop/CLI.
    session_id = str(uuid.uuid4())[:8]
    env_file = os.environ.get('CLAUDE_ENV_FILE', '')
    if env_file:
        with open(env_file, 'a', encoding='utf-8') as f:
            f.write(f'KG_SESSION_ID={session_id}\n')
    print(f'[kg] Session ID: {session_id}')


# ── session-stop ──────────────────────────────────────────────────────────────

def session_stop(repo_root: Path) -> None:
    graph_path   = repo_root / '.claude' / 'knowledge-graph.json'
    context_file = repo_root / 'CONTEXT.md'

    if not graph_path.exists():
        return

    graph_rel = str(graph_path.relative_to(repo_root))

    if not graph_is_dirty(repo_root, graph_rel):
        return  # nothing to do

    print('[kg] Knowledge graph has uncommitted changes — auto-committing')

    # Regenerate CONTEXT.md from the updated graph
    stdout, _, rc = kg(repo_root, 'summary')
    if rc == 0:
        context_file.write_text(stdout, encoding='utf-8')

    context_rel = str(context_file.relative_to(repo_root))
    git_run(repo_root, 'git', 'add', graph_rel, context_rel)

    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    result = git_run(
        repo_root, 'git', 'commit',
        '-m', f'chore: update knowledge graph [auto-commit {now}]',
    )

    if result.returncode != 0:
        print(f'[kg] Auto-commit failed: {result.stderr.strip()}')
        return

    print('[kg] Graph committed')

    # Push to the current tracking branch
    branch_r = git_run(repo_root, 'git', 'rev-parse', '--abbrev-ref', 'HEAD')
    branch   = branch_r.stdout.strip()
    push     = git_run(repo_root, 'git', 'push', 'origin', branch)

    if push.returncode == 0:
        print(f'[kg] Graph pushed → {branch}')
    else:
        # Non-fatal: log and let the global stop hook surface the push failure
        print(f'[kg] Push failed (will retry via global hook): {push.stderr.strip()[:200]}')


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    repo_root = find_repo_root()

    if repo_root is None:
        print(f'[kg] Not inside a git repo — skipping {cmd}')
        sys.exit(0)

    if cmd == 'session-start':
        session_start(repo_root)
    elif cmd == 'session-stop':
        session_stop(repo_root)
    else:
        sys.exit(f'[kg] Unknown hook: {cmd}. Available: session-start, session-stop')


if __name__ == '__main__':
    main()
