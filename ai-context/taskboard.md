# Taskboard — H4YF

> Update status here whenever a task changes. Use `handoff.md` for session narrative.

## Next Session Prompt

> Paste this at the start of the next Claude or Gemini session.

```
Read ai-context/handoff.md and ai-context/taskboard.md first.

Current state: Drive sync is live (gdrive:H4YF/ai-context), rclone is
configured in the container, PR #5 is merged into main. All infrastructure
is complete.

Session goal: Work through docs/brand-brief.md with the user to define
H4YF brand identity — name meaning, business description, target customer,
brand personality, visual direction, eCommerce platform choice, and launch
goals. Record confirmed facts in ai-context/memory.md as we go. Update
taskboard.md when items are checked off. Push to Drive at session end.
```

## In Progress
_(none)_

## Todo — Setup (must complete in order)
- [x] 2026-06-21 — Fix Stop hook: removed hardcoded path from `.claude/settings.json`
- [x] 2026-06-21 — Install rclone in Linux container (via apt)
- [x] 2026-06-21 — Configure rclone `gdrive` remote with OAuth token
- [x] 2026-06-21 — Run initial Drive sync — 7 files pushed to `gdrive:H4YF/ai-context`
- [x] 2026-06-21 — Verified files visible at `gdrive:H4YF/ai-context` ✓
- [x] 2026-07-04 — Merge branch `claude/gemini-offline-drive-sync-gur4we` → main (PR #5)

## Todo — Alignment Fixes (from session review 2026-06-21)
- [x] 2026-06-21 — Conflict resolution strategy documented in `harness.md` (sequential work assumed; human decides on true conflicts)
- [x] 2026-06-21 — Session log gitignore policy decided: tracked in git by default, opt-out documented in `.gitignore`
- [ ] Test bisync `--first-run` detection on actual machine with rclone installed
- [ ] PostToolUse auto-commit hook — deferred; manual pull workflow sufficient for now

## Todo — H4YF Project
- [ ] Fill in `docs/brand-brief.md` — name, business, personality, visual direction, eCommerce, launch goals
- [ ] Copy brand facts to `ai-context/memory.md` once brief is settled
- [ ] Choose eCommerce platform (brief section 5)
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
- [x] 2026-06-21 — memory.md updated with full session learnings (Windows env, rclone decisions, conventions)
- [x] 2026-06-21 — docs/brand-brief.md created as brand discovery template
- [x] 2026-07-04 — Fixed drive-sync.sh `pull` bug (was destructive `rclone sync`, now safe `rclone copy`)
- [x] 2026-07-04 — Installed + authenticated rclone on Mac; verified Drive sync live
- [x] 2026-07-04 — Set up Gemini API bridge on Mac: primary key copied from PC, Mac-portability bug fixed (ubiq-scripts PR #4), 2 more account keys added (3-key rotation pool total), verified with real prompts

## Backlog
- [ ] Payment processing integration
- [ ] Order management system
- [ ] Customer account system
- [ ] Analytics and reporting
