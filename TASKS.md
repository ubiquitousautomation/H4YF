# H4YF — Task Board

---

## Now: Finish Drive Setup

> **Windows / VS Code users:** The scripts are bash — they won't run in PowerShell.
> Open a **Git Bash** terminal instead (click `+` dropdown in VS Code terminal panel → Git Bash).

These three steps must happen in order.

---

### Step 1 — Authenticate rclone with Google Drive

The Claude Code environment has no browser, so auth must be done on your local machine first,
then the token is pasted into the container.

**On your local machine (Git Bash / WSL / Mac terminal):**

```bash
# Install rclone if you don't have it — https://rclone.org/install/
# Then run:
rclone authorize "drive"
```

> A browser opens. Sign in as `ubiquitousautomation@gmail.com` and allow access.
> When done, rclone prints a JSON token in your terminal. **Copy the entire JSON blob.**

**Back in the Claude Code terminal (Linux container):**

```bash
rclone config create gdrive drive scope drive token '<paste-token-json-here>'
```

> Confirm it worked:
> ```bash
> rclone lsd gdrive:
> ```
> You should see your Google Drive root folders listed.

---

### Step 2 — Push context files to Drive

```bash
bash ./scripts/drive-sync.sh push
```

> Uploads `ai-context/` to `My Drive > H4YF > ai-context`.
> After this, Gemini can see all five files.

---

### Step 3 — Verify + merge

- Open Google Drive and confirm `H4YF/ai-context/` contains:
  `harness.md` · `memory.md` · `handoff.md` · `taskboard.md` · `sessions/`
- Merge **PR #5** → `main`:
  https://github.com/ubiquitousautomation/H4YF/pull/5

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
# Start of session (in Claude Code terminal)
bash ./scripts/drive-sync.sh pull    # get Gemini's latest edits, if any

# End of session — fires automatically via Stop hook, but you can also run:
bash ./scripts/drive-sync.sh push
```

---

## Open Questions (document answers in harness.md when decided)

- **Auto-commit after pull** — after `drive-sync.sh pull`, auto-commit changes to git?
  Keeps history tight. Would need a PostToolUse hook. Currently deferred.
- **bisync first-run** — verify the `--first-run` auto-detection works once rclone is live.

---

## Done

| Date | What |
|------|------|
| 2026-06-21 | Repo initialized |
| 2026-06-21 | AI context files created (harness, memory, handoff, taskboard, sessions) |
| 2026-06-21 | Drive sync scripts written (rclone push / pull / bisync / fullsync / status) |
| 2026-06-21 | Claude Code Stop hook configured (auto-push on session end) |
| 2026-06-21 | CLAUDE.md + GEMINI.md entrypoints added |
| 2026-06-21 | Alignment review: 6 bugs fixed (push safety, bisync first-run, setup flag, GEMINI.md, hardcoded path, .gitignore) |
| 2026-06-21 | Conflict resolution strategy documented in harness.md |
| 2026-06-21 | Session log written (sessions/2026-06-21-claude.md) |
| 2026-06-21 | setup-drive.sh updated: Windows note, headless token flow, display detection |
| 2026-06-21 | TASKS.md updated with Windows + headless auth instructions |
