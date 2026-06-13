# H4YF Knowledge Graph Context
*Auto-generated from .claude/knowledge-graph.json — 2026-06-13 16:18 UTC*
*4 nodes · 3 edges*

## Decision Nodes
- **Knowledge Graph Architecture** (`kg-arch-`): Adopted file-based JSON knowledge graph with Python CLI for persistent cross-session memory. Stored in .claude/knowledge-graph.json and committed to git for versioning.

## Component Nodes
- **Claude Code Harness** (`harness-`): SessionStart/Stop hooks, skills, and MCP servers that govern the development workflow. Global hooks handle git identity and commit validation; project hooks regenerate CONTEXT.md from the knowledge graph.
- **Knowledge Graph CLI (kg.py)** (`kg-tool-`): Python CLI at .claude/scripts/kg.py for querying and updating the knowledge graph. Subcommands: summary, add-node, add-edge, list, query.

## Entity Nodes
- **H4YF (HEAT4YAFEAT)** (`h4yf-bra`): Core brand entity — eCommerce brand establishment project

## Relationships
- **Knowledge Graph Architecture** `part_of` **Claude Code Harness** — Knowledge graph is an enhancement layered onto the Claude Code harness
- **Knowledge Graph CLI (kg.py)** `implements` **Knowledge Graph Architecture** — kg.py is the concrete implementation of the graph architecture
- **Claude Code Harness** `relates_to` **H4YF (HEAT4YAFEAT)** — Harness drives development of the H4YF brand platform

## Recent Activity
- [2026-06-13] Entity: **H4YF (HEAT4YAFEAT)**
- [2026-06-13] Decision: **Knowledge Graph Architecture**
- [2026-06-13] Component: **Claude Code Harness**
- [2026-06-13] Component: **Knowledge Graph CLI (kg.py)**

---
*Update the graph: `python3 .claude/scripts/kg.py add-node TYPE NAME DESC`*
*Regenerate: `python3 .claude/scripts/kg.py summary > CONTEXT.md`*
