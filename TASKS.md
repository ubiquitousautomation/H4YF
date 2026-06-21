# H4YF — Task Board

---

## Now: Finish Drive Setup

These three must happen in order, and all require a browser on your local machine.

**1. Authenticate with Google Drive**

```bash
./scripts/setup-drive.sh
```

> Installs rclone if needed, opens Google OAuth in a browser.
> Sign in as `ubiquitousautomation@gmail.com`.

---

**2. Push context files to Drive**

```bash
./scripts/drive-sync.sh push
```

> Uploads `ai-context/` to `My Drive > H4YF > ai-context`.
> After this, Gemini can see all five files.

---

**3. Verify Gemini access + merge PR**

- Open Google Drive and confirm `H4YF/ai-context/` contains:
  `harness.md` · `memory.md` · `handoff.md` · `taskboard.md` · `sessions/`
- Merge PR #5 → `main`:
  https://github.com/ubiquitousautomation/H4YF/pull/5

---

## Decisions Needed (no rush, but document in harness.md when decided)

- **Conflict resolution** — if both Claude and Gemini edit the same file before a sync, which version wins? Options: last-write-wins (default), bisync merge, manual.
- **Session log retention** — session `.md` files in `ai-context/sessions/` are currently tracked in git. Add them to `.gitignore` if you'd rather keep them Drive-only.
- **Auto-commit hook** — after a `drive-sync.sh pull`, auto-commit the changes to git? Keeps history tighter. Needs a PostToolUse hook.

---

## Up Next: H4YF Project Work

- [ ] Brand identity — name, voice, visual direction
- [ ] eCommerce platform choice — Shopify, custom, other?
- [ ] Domain + hosting setup
- [ ] Product catalog structure
- [ ] Brand assets — logo, palette, typography

---

## Backlog

- [ ] Payment processing
- [ ] Order management
- [ ] Customer accounts
- [ ] Analytics

---

## Daily Workflow (once Drive is live)

```bash
# Start of session
./scripts/drive-sync.sh pull    # get Gemini's latest edits (if any)

# End of session — automatic via Stop hook, but you can also run manually:
./scripts/drive-sync.sh push
```

---

## Done

| Date | What |
|------|------|
| 2026-06-21 | Repo initialized |
| 2026-06-21 | AI context files created (harness, memory, handoff, taskboard, sessions) |
| 2026-06-21 | Drive sync scripts written (rclone push / pull / bisync / fullsync) |
| 2026-06-21 | Claude Code Stop hook configured (auto-push on session end) |
| 2026-06-21 | CLAUDE.md + GEMINI.md entrypoints added |
| 2026-06-21 | Alignment review: 6 bugs fixed (push safety, bisync first-run, setup flag, GEMINI.md pull claim, hardcoded path, .gitignore) |
