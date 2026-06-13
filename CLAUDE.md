# H4YF — HEAT4YAFEAT

Brand establishment and eCommerce platform for HEAT4YAFEAT.

---

## Session Start Protocol

**Always read `CONTEXT.md` before proceeding.** It is auto-generated from the knowledge graph at session start and captures all prior decisions, components, and relationships.

```
cat CONTEXT.md
```

If `CONTEXT.md` is missing or stale, regenerate it:

```
python3 .claude/scripts/kg.py summary > CONTEXT.md
```

---

## Knowledge Graph

This project uses a persistent, git-versioned knowledge graph (`.claude/knowledge-graph.json`) for cross-session memory. Every significant decision, component, or relationship must be recorded. The graph compounds — each session builds on what prior sessions wrote.

### Design principles

- **No external services** — Python 3 stdlib only; runs on Mac, Linux, Windows, web, desktop, CLI
- **Platform-agnostic invocation** — all hooks call `python3 .claude/scripts/hooks.py`; on Windows substitute `python` if `python3` is not on PATH
- **Model-agnostic** — the graph is the memory layer; Claude is just the reader/writer
- **Client-agnostic** — the `.claude/` scaffold is portable to any project; use `kg.py init` to start fresh

### When to update the graph

Update during the session, not only at the end:

- Architectural or product decisions made
- New components, features, or services designed or built
- Relationships between entities discovered or established
- Prior decisions superseded or revised
- Status of a node changes (deprecated, superseded)

### Knowledge graph commands

```bash
# ── Nodes ────────────────────────────────────────────────────────
python3 .claude/scripts/kg.py add-node Decision   "name" "description"
python3 .claude/scripts/kg.py add-node Component  "name" "description"
python3 .claude/scripts/kg.py add-node Feature    "name" "description"
python3 .claude/scripts/kg.py add-node Entity     "name" "description"
python3 .claude/scripts/kg.py add-node Concept    "name" "description"

python3 .claude/scripts/kg.py update-node <id> description "new text"
python3 .claude/scripts/kg.py update-node <id> status deprecated
python3 .claude/scripts/kg.py remove-node <id>

# ── Edges (use 8-char ID prefix from list output) ─────────────────
python3 .claude/scripts/kg.py add-edge <src-id> <relationship> <tgt-id> "notes"
# Relationships: depends_on | implements | supersedes | relates_to | part_of | created_by

# ── Query ─────────────────────────────────────────────────────────
python3 .claude/scripts/kg.py list [TYPE]        # list all or by type
python3 .claude/scripts/kg.py query "term"       # search name/description/tags
python3 .claude/scripts/kg.py neighbors <id>     # show connected nodes

# ── Maintenance ───────────────────────────────────────────────────
python3 .claude/scripts/kg.py validate           # check integrity
python3 .claude/scripts/kg.py diff               # what changed since last commit
python3 .claude/scripts/kg.py summary > CONTEXT.md   # regenerate context

# ── Bootstrap a new client project ────────────────────────────────
python3 .claude/scripts/kg.py init "ProjectName" "Description"
```

### Commit graph changes

The session-stop hook auto-commits and pushes if the graph is dirty. To commit manually:

```bash
python3 .claude/scripts/kg.py summary > CONTEXT.md
git add .claude/knowledge-graph.json CONTEXT.md
git commit -m "chore: update knowledge graph"
```

---

## Harness Architecture

```
Session starts
  → hooks.py session-start
      validate graph
      regenerate CONTEXT.md
      export KG_SESSION_ID (web/remote sessions)

During session
  → Claude reads CONTEXT.md for accumulated project knowledge
  → kg.py add-node / add-edge / update-node as decisions are made

Session ends
  → hooks.py session-stop
      detect dirty graph
      print session summary (nodes added this session)
      auto-commit + push
  → global stop hook validates clean git state
```

**Recursive memory loop**: session updates graph → graph committed → next session reads CONTEXT.md → cycle repeats indefinitely across any device, model, or client.

### Hook entry points

| Hook | Command in settings.json |
|------|--------------------------|
| SessionStart | `python3 .claude/scripts/hooks.py session-start` |
| Stop | `python3 .claude/scripts/hooks.py session-stop` |

**Windows**: replace `python3` with `python` if needed. The hooks use `sys.executable` internally so all subprocess calls are consistent once the runner starts.

### Node types

| Type | Use for |
|------|---------|
| `Decision` | Architectural or product decisions |
| `Component` | Code modules, services, scripts |
| `Feature` | Product features |
| `Entity` | Brand, product, person, business entity |
| `Concept` | Abstract principles or patterns |

### Relationship types

| Relationship | Meaning |
|---|---|
| `depends_on` | A requires B to function |
| `implements` | A is a concrete realisation of B |
| `supersedes` | A replaces B |
| `relates_to` | General association |
| `part_of` | A is a sub-component of B |
| `created_by` | A was authored by B |

---

## Project Overview

H4YF is in early-stage development. Current state is always in `CONTEXT.md`.

Key files:

| Path | Purpose |
|------|---------|
| `.claude/knowledge-graph.json` | Versioned graph store |
| `.claude/scripts/kg.py` | Graph CLI (stdlib only) |
| `.claude/scripts/hooks.py` | Cross-platform hook runner |
| `.claude/scripts/session-start.sh` | Thin bash wrapper → hooks.py |
| `.claude/scripts/session-stop.sh` | Thin bash wrapper → hooks.py |
| `.claude/settings.json` | Project hook registrations |
| `CONTEXT.md` | Auto-generated session context |
