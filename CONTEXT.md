# H4YF Knowledge Graph Context
*Auto-generated — 2026-06-13 17:26 UTC*
*6 active nodes · 6 edges*

## Decision Nodes
- **Knowledge Graph Architecture** (`kg-arch-`): File-based JSON knowledge graph with Python CLI for persistent cross-session memory. Stored in .claude/knowledge-graph.json, committed to git for versioning. No external services required.
- **Python Hook Runner over Bash** (`decision`): Chose Python (hooks.py) over bash scripts for hooks to achieve device/platform/model-agnostic harness. Bash scripts excluded Windows; Python 3 is available on all Claude Code platforms.

## Component Nodes
- **Claude Code Harness** (`harness-`): SessionStart/Stop hooks, skills, and MCP servers governing the development workflow. Global hooks: git identity + commit validation. Project hooks: knowledge graph lifecycle (CONTEXT.md regeneration, auto-commit on stop).
- **Knowledge Graph CLI (kg.py)** (`kg-tool-`): Python CLI at .claude/scripts/kg.py. Subcommands: summary, add-node, update-node, remove-node, add-edge, list, query, neighbors, validate, init. Python stdlib only — no pip installs.
- **Cross-platform Hook Runner (hooks.py)** (`hooks-ru`): Single Python entry point for all Claude Code project hooks (.claude/scripts/hooks.py). Handles session-start (validate, regenerate CONTEXT.md, export session ID) and session-stop (auto-commit/push graph if dirty). Uses sys.executable — no PATH assumptions, works on Mac/Linux/Windows.

## Entity Nodes
- **H4YF (HEAT4YAFEAT)** (`h4yf-bra`): Core brand entity — eCommerce brand establishment project

## Relationships
- **Knowledge Graph Architecture** `part_of` **Claude Code Harness** — Knowledge graph is an enhancement layered onto the Claude Code harness
- **Knowledge Graph CLI (kg.py)** `implements` **Knowledge Graph Architecture** — kg.py is the concrete implementation of the graph architecture
- **Claude Code Harness** `relates_to` **H4YF (HEAT4YAFEAT)** — Harness drives development of the H4YF brand platform
- **Cross-platform Hook Runner (hooks.py)** `part_of` **Claude Code Harness** — hooks.py is the project-level hook layer within the harness
- **Cross-platform Hook Runner (hooks.py)** `depends_on` **Knowledge Graph CLI (kg.py)** — hooks.py calls kg.py for validate and summary operations
- **Python Hook Runner over Bash** `implements` **Cross-platform Hook Runner (hooks.py)** — hooks.py is the implementation of the cross-platform hook decision

## Recent Activity
- [2026-06-13] Component: **Cross-platform Hook Runner (hooks.py)**
- [2026-06-13] Decision: **Python Hook Runner over Bash**
- [2026-06-13] Entity: **H4YF (HEAT4YAFEAT)**
- [2026-06-13] Decision: **Knowledge Graph Architecture**
- [2026-06-13] Component: **Claude Code Harness**
- [2026-06-13] Component: **Knowledge Graph CLI (kg.py)**

---
*Update: `python3 .claude/scripts/kg.py add-node TYPE NAME DESC`*
*Regenerate: `python3 .claude/scripts/kg.py summary > CONTEXT.md`*
