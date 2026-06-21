# H4YF — HEAT4YAFEAT (Gemini Context)

## Project
Brand Establishment and eCommerce platform.
GitHub: `ubiquitousautomation/H4YF`

## Where Your Files Live on Google Drive
All context files are under `H4YF/ai-context/` in the shared Google Drive.

| File | Purpose |
|------|---------|
| `harness.md` | Rules and constraints for all AI agents |
| `memory.md` | Persistent facts — **append only, never delete** |
| `handoff.md` | Current state — **read this first every session** |
| `taskboard.md` | Active tasks and status |
| `sessions/` | Per-session log archive |

## Session Protocol
1. Open `H4YF/ai-context/handoff.md` on Google Drive — read the current state
2. Check `taskboard.md` for active tasks
3. Do work
4. Append any new persistent facts to `memory.md` (date each entry)
5. Rewrite `handoff.md` to reflect what you did and what comes next
6. Update task status in `taskboard.md`
7. (Optional) Save a session summary to `sessions/YYYY-MM-DD-<agent>.md`

## Harness Rules (from harness.md)
- Never delete from `memory.md` — only append
- Keep `handoff.md` under 500 words
- Always date your entries (`YYYY-MM-DD`)
- Use the taskboard; don't track tasks in handoff

## Sync Note
Changes you make on Google Drive will be pulled into the git repo automatically
when a Claude Code session starts. Changes Claude makes will be pushed to Drive
when Claude's session ends.
