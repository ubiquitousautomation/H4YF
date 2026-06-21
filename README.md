# H4YF — HEAT4YAFEAT

Brand Establishment and eCommerce platform.

---

## AI Agent Setup

This repo uses a two-agent workflow: **Claude** (via Claude Code) for development, and **Gemini** (via Google Drive) for shared context. Both agents read and write the same five files under `ai-context/`, which sync between git and Google Drive via rclone.

| File | Purpose |
|------|---------|
| `ai-context/harness.md` | Rules and constraints for all AI agents |
| `ai-context/memory.md` | Persistent facts across sessions (append-only) |
| `ai-context/handoff.md` | Current state — read this first every session |
| `ai-context/taskboard.md` | Active tasks and status |
| `ai-context/sessions/` | Per-session log archive |

Claude auto-pushes `ai-context/` to Google Drive at the end of every session via a Stop hook. Gemini reads and writes directly on Drive. Claude pulls at the start of a session when Gemini has made changes.

## Getting Started

**First time — set up Google Drive sync:**

See `TASKS.md` for step-by-step instructions, including the Windows / headless token flow.

Short version (requires rclone installed locally):
```bash
# On your local machine
rclone authorize "drive"
# Copy the JSON token it prints, then in the Claude Code terminal:
rclone config create gdrive drive scope drive token '<token-json>'

# Then push context files to Drive
bash ./scripts/drive-sync.sh push
```

**Every session (Claude):**
```bash
bash ./scripts/drive-sync.sh pull   # pull Gemini's latest edits (if any)
# ... do work ...
# push fires automatically on session end via Stop hook
```

**Every session (Gemini):**
Open `H4YF/ai-context/handoff.md` on Google Drive. Follow the protocol in `GEMINI.md`.

## Repo Structure

```
H4YF/
├── ai-context/          # Shared AI context (git + Drive synced)
│   ├── harness.md
│   ├── memory.md
│   ├── handoff.md
│   ├── taskboard.md
│   └── sessions/
├── scripts/
│   ├── drive-sync.sh    # push / pull / bisync / fullsync / status
│   └── setup-drive.sh   # one-time rclone + Google OAuth setup
├── .claude/
│   └── settings.json    # Stop hook + permissions
├── CLAUDE.md            # Claude session protocol
├── GEMINI.md            # Gemini session protocol
└── TASKS.md             # Human-readable task board (start here)
```

## Current Status

See `TASKS.md` for the live task board and next steps.
