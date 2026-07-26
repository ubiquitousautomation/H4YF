# AI Agent Harness — H4YF

## Project Identity
- **Name**: HEAT4YAFEAT (H4YF)
- **Domain**: Brand Establishment and eCommerce
- **Repo**: `ubiquitousautomation/H4YF` (GitHub)
- **Owner**: ubiquitousautomation@gmail.com

## Active AI Agents
| Agent | Platform | Access Method |
|-------|----------|---------------|
| Claude | Anthropic / Claude Code | Git repo + filesystem |
| Gemini | Google | Google Drive sync (`gdrive:H4YF/ai-context`) |

## Session Rules (All Agents)
1. **Start**: Read `handoff.md` before doing anything else
2. **Memory**: Append new persistent facts to `memory.md` with a date — never delete entries
3. **Tasks**: Update `taskboard.md` when task status changes
4. **End**: Rewrite `handoff.md` to reflect current state and next steps
5. **Archive**: Optionally save a session summary to `sessions/YYYY-MM-DD-<agent>.md`

## Constraints
- Keep `handoff.md` under 500 words (archive detail to `sessions/`)
- Track tasks in `taskboard.md`, not `handoff.md`
- All date entries use `YYYY-MM-DD` format
- Don't delete from `memory.md` — mark stale entries `[SUPERSEDED]` instead

## Conflict Resolution
Sequential work is assumed — one agent works at a time. If both agents edit
the same file before a sync, the following rules apply:

- **`push` / `pull`** (rclone copy): additive only, never overwrites — no true conflict possible
- **`bisync`**: rclone's default is last-modified-wins; use only when you know what changed
- **Real conflict** (same file edited on both sides between syncs): human decides — do not let
  either agent silently overwrite; run `./scripts/drive-sync.sh status` to inspect, then
  manually merge or pick a winner before the next push/pull

**Best practice**: finish your session and push/pull before the other agent starts.

## Drive Sync
- Local: `ai-context/` in this git repo
- Remote: `gdrive:H4YF/ai-context` (rclone remote `gdrive`)
- Claude auto-pushes on session Stop (`.claude/settings.json` hook)
- Claude should pull at session start: `./scripts/drive-sync.sh pull`
- Gemini reads/writes directly on Google Drive

## Tool Permissions (Claude)
- `Bash(bash scripts/drive-sync.sh*)` — allowed
- `Bash(bash scripts/setup-drive.sh*)` — allowed
- `Bash(rclone*)` — allowed
