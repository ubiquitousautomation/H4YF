# H4YF — HEAT4YAFEAT

Brand establishment and eCommerce platform for HEAT4YAFEAT.

## Session Start Protocol

**Always read `CONTEXT.md` before proceeding.** It is auto-generated from the knowledge graph at session start and captures all prior decisions, components, and relationships.

```bash
cat CONTEXT.md
```

## Knowledge Graph

This project uses a persistent, git-versioned knowledge graph (`.claude/knowledge-graph.json`) for cross-session memory. Every significant decision, component, or relationship should be recorded. The graph compounds — each session builds on what prior sessions wrote.

### When to update the graph

- Architectural or product decisions made
- New components, features, or services designed or built
- Relationships between entities discovered or established
- Prior decisions superseded or revised

### How to update the graph

```bash
# Add a node
python3 .claude/scripts/kg.py add-node Decision "name" "description"
python3 .claude/scripts/kg.py add-node Component "name" "description"
python3 .claude/scripts/kg.py add-node Feature "name" "description"
python3 .claude/scripts/kg.py add-node Entity "name" "description"
python3 .claude/scripts/kg.py add-node Concept "name" "description"

# Add a relationship (use the 8-char ID prefix shown in list output)
python3 .claude/scripts/kg.py add-edge <src-id> <relationship> <tgt-id> "optional notes"

# Relationships: depends_on | implements | supersedes | relates_to | part_of | created_by

# List all nodes
python3 .claude/scripts/kg.py list

# Search nodes
python3 .claude/scripts/kg.py query "ecommerce"

# Regenerate CONTEXT.md after updates
python3 .claude/scripts/kg.py summary > CONTEXT.md
```

### Commit graph changes before session end

```bash
git add .claude/knowledge-graph.json CONTEXT.md
git commit -m "chore: update knowledge graph"
```

## Project Overview

H4YF is in early-stage development. Current state is tracked in `CONTEXT.md`.

## Architecture Notes

- **Graph backend**: File-based JSON (`.claude/knowledge-graph.json`), committed to git for versioning and history
- **No external services required** — Python stdlib only, runs in any environment
- **SessionStart hook** regenerates `CONTEXT.md` from the graph automatically
- **Recursive memory loop**: session updates graph → graph committed → next session reads CONTEXT.md → cycle repeats
