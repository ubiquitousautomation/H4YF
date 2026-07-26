# H4YF — HEAT4YAFEAT

## Project
Brand Establishment and eCommerce platform.
Repo: `ubiquitousautomation/H4YF`

**Two memory systems now coexist here — both run, both are session-start reads.** They were
built independently (PR #2 added the knowledge graph on top of the existing Drive/Gemini
system) and serve different purposes: `ai-context/` is the human/Gemini-readable handoff log;
the knowledge graph is a structured, queryable node/edge store. Do not pick one and drop the
other — see Session Start Protocol below for the combined read order.

## Project Overview

H4YF (HEAT4YAFEAT) is a sneaker and streetwear brand expanding its eCommerce presence onto Whatnot (live shopping/auction platform). The business is already established on eBay and StockX and is now building a live-selling channel to capture community, real-time price discovery, and higher margins through direct buyer relationships.

## Brand Identity

- **Name:** HEAT4YAFEAT / H4YF
- **Niche:** Sneakers (Jordans, Nike SB, Adidas, New Balance, collabs) + streetwear (Supreme, Off-White, Palace, etc.)
- **Voice:** Hype, authentic, knowledgeable — the plug in your city that went online
- **Positioning:** Verified, authenticated heat — not a flip house, a curation brand

## Key Objectives

1. Reach Whatnot **Top Seller** status within 90 days of first show
2. Drive 30%+ of revenue through Whatnot within 6 months (vs. eBay/StockX)
3. Build a repeat-buyer community — target 40% returning buyers by month 3
4. Establish H4YF as the go-to live sneaker plug on Whatnot

## Platform Context

| Platform | Fee Structure | Speed | Community |
|----------|--------------|-------|-----------|
| StockX   | ~9.5% seller fee + shipping | Days | None |
| eBay     | ~12.9% + shipping | Days | Low |
| Whatnot  | ~8% + $0.30/transaction | Real-time | High |

Whatnot's fee advantage + community upside is the core thesis for this expansion.

*Figures above are this doc's original numbers (kept for provenance). More precise, currently-verified fee schedules for Whatnot, eBay, and Depop — with exact tier breakpoints and per-price-point comparisons — are in `marketing/content-guides/HEAT4YAFEAT_Depop_SOP — Shop Operations, Listing & Distribution Guide [v3].docx` §1.2. Use that table over this one for anything fee-sensitive.*

## Working Conventions

- All strategy docs live in `docs/playbook/`
- Use ISO dates (YYYY-MM-DD) for any scheduling references
- Keep pricing data and margin math in `pricing-strategy.md` — single source of truth
- Update `whatnot-launch-strategy.md` KPI table after each show week

---

## Session Start Protocol

1. **Read `CONTEXT.md`** — auto-generated from the knowledge graph at session start, captures
   prior decisions, components, and relationships:
   ```
   cat CONTEXT.md
   ```
   If missing or stale, regenerate: `python3 .claude/scripts/kg.py summary > CONTEXT.md`
2. **Read `ai-context/handoff.md`** — current state, read this first for anything Gemini or a
   prior session left mid-flight.
3. `./scripts/drive-sync.sh pull` — get latest `ai-context/` from Google Drive (Gemini may have
   written since your last session).
4. Do work — update both systems as you go, not only at the end (see below).
5. Update `ai-context/handoff.md` and `ai-context/taskboard.md`; append new facts to
   `ai-context/memory.md`.
6. `./scripts/drive-sync.sh push` — also fires automatically on the Stop hook, alongside the
   knowledge-graph auto-commit (both are registered in `.claude/settings.json`).

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
  → scripts/drive-sync.sh push
      pushes ai-context/ to Google Drive (Gemini's read surface)
  → global stop hook validates clean git state
```

**Recursive memory loop**: session updates graph → graph committed → next session reads CONTEXT.md → cycle repeats indefinitely across any device, model, or client. In parallel, `ai-context/` syncs to Drive so Gemini stays current on the same session's work.

### Hook entry points

| Hook | Command in settings.json |
|------|--------------------------|
| SessionStart | `python3 .claude/scripts/hooks.py session-start` |
| Stop | `python3 .claude/scripts/hooks.py session-stop` **then** `bash scripts/drive-sync.sh push` |

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

H4YF is in early-stage development. Current state is always in `CONTEXT.md` (knowledge graph) and `ai-context/handoff.md` (Drive/Gemini system) — check both, they cover different things.

Key files:

| Path | Purpose |
|------|---------|
| `.claude/knowledge-graph.json` | Versioned graph store |
| `.claude/scripts/kg.py` | Graph CLI (stdlib only) |
| `.claude/scripts/hooks.py` | Cross-platform hook runner |
| `.claude/scripts/session-start.sh` | Thin bash wrapper → hooks.py |
| `.claude/scripts/session-stop.sh` | Thin bash wrapper → hooks.py |
| `.claude/settings.json` | Project hook registrations |
| `CONTEXT.md` | Auto-generated session context (from the knowledge graph) |
| `ai-context/harness.md` | Rules and constraints for all AI agents |
| `ai-context/memory.md` | Persistent facts across sessions (append-only) |
| `ai-context/handoff.md` | Current state — Gemini/Drive side |
| `ai-context/taskboard.md` | Active tasks and status |
| `ai-context/sessions/` | Per-session logs (archive) |

## Google Drive Sync
- Local: `ai-context/` in this repo
- Remote: `gdrive:H4YF/ai-context` (rclone remote named `gdrive`)
- First-time setup: `./scripts/setup-drive.sh`
- Manual sync: `./scripts/drive-sync.sh [push|pull|bisync]`
- Auto-push: fires on every Claude Code session Stop via `.claude/settings.json` hook

## Social API Scripts

`social_apis/` — PowerShell 5.1 scripts for YouTube, Meta (Instagram/Facebook), and TikTok.
Each script reads credentials from a local secrets path (never committed) — see
`social_apis/SETUP_GUIDE.md` for the per-platform credential setup. These predate and are
independent of both memory systems above; they are plain automation scripts, not part of the
knowledge graph or ai-context.

## Gemini Access
Gemini reads/writes `ai-context/` files via Google Drive. See `GEMINI.md` for its session protocol. Gemini does not read or write the knowledge graph — that system is Claude-only for now.
