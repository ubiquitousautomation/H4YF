# Taskboard — H4YF

> Update status here whenever a task changes. Use `handoff.md` for session narrative.

## In Progress
_(none)_

## Todo — Setup (must complete in order)
- [x] 2026-06-21 — Fix Stop hook: removed hardcoded path from `.claude/settings.json`
- [ ] Configure rclone `gdrive` remote — run `./scripts/setup-drive.sh` (needs browser for Google OAuth)
- [ ] Run initial Drive sync — `./scripts/drive-sync.sh push`
- [ ] Verify Gemini can access files at `H4YF/ai-context/` on Google Drive
- [ ] Merge branch `claude/gemini-offline-drive-sync-gur4we` → main

## Todo — Alignment Fixes (from session review 2026-06-21)
- [x] 2026-06-21 — Conflict resolution strategy documented in `harness.md` (sequential work assumed; human decides on true conflicts)
- [x] 2026-06-21 — Session log gitignore policy decided: tracked in git by default, opt-out documented in `.gitignore`
- [ ] Test bisync `--first-run` detection on actual machine with rclone installed
- [ ] PostToolUse auto-commit hook — deferred; manual pull workflow sufficient for now

## Todo — H4YF Project
- [ ] Define brand identity (name, voice, visual direction)
- [ ] Choose eCommerce platform (Shopify / custom / other)
- [ ] Set up domain and hosting
- [ ] Create product catalog structure
- [ ] Design brand assets (logo, color palette, typography)

## Done
- [x] 2026-06-21 — Initialize git repository
- [x] 2026-06-21 — Create AI context file structure (harness, memory, handoff, taskboard, sessions)
- [x] 2026-06-21 — Write Google Drive sync scripts (rclone)
- [x] 2026-06-21 — Configure Claude Code Stop hook for auto-push to Drive
- [x] 2026-06-21 — Add CLAUDE.md and GEMINI.md entrypoints
- [x] 2026-06-21 — Session alignment review: fixed 6 bugs (push safety, bisync first-run, setup-drive --all flag, GEMINI.md pull claim, .gitignore, hardcoded Stop hook path)
- [x] 2026-06-21 — Conflict resolution strategy documented in harness.md
- [x] 2026-06-21 — Session log for this session written to sessions/2026-06-21-claude.md
- [x] 2026-06-21 — Handoff updated to current state

## Backlog
- [ ] Payment processing integration
- [ ] Order management system
- [ ] Customer account system
- [ ] Analytics and reporting
