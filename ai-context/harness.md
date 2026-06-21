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
