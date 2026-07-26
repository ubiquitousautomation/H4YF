# H4YF — HEAT4YAFEAT

## Project
Brand Establishment and eCommerce platform.
Repo: `ubiquitousautomation/H4YF`

## AI Context Files
All shared AI context lives in `ai-context/`. These files sync to Google Drive
so Gemini can also read and update them.

| File | Purpose |
|------|---------|
| `ai-context/harness.md` | Rules and constraints for all AI agents |
| `ai-context/memory.md` | Persistent facts across sessions (append-only) |
| `ai-context/handoff.md` | Current state — **read this first every session** |
| `ai-context/taskboard.md` | Active tasks and status |
| `ai-context/sessions/` | Per-session logs (archive) |

## Session Protocol
1. `./scripts/drive-sync.sh pull` — get latest from Google Drive
2. Read `ai-context/handoff.md`
3. Do work
4. Update `ai-context/handoff.md` and `ai-context/taskboard.md`
5. Append new facts to `ai-context/memory.md`
6. `./scripts/drive-sync.sh push` — (also fires automatically on Stop hook)

## Google Drive Sync
- Local: `ai-context/` in this repo
- Remote: `gdrive:H4YF/ai-context` (rclone remote named `gdrive`)
- First-time setup: `./scripts/setup-drive.sh`
- Manual sync: `./scripts/drive-sync.sh [push|pull|bisync]`
- Auto-push: fires on every Claude Code session Stop via `.claude/settings.json` hook

## Gemini Access
Gemini reads/writes these files via Google Drive. See `GEMINI.md` for its session protocol.
