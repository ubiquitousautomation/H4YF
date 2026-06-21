# Persistent AI Memory — H4YF

> Append-only. Never delete entries. Mark stale facts `[SUPERSEDED]`.
> Date every entry: `YYYY-MM-DD`.

## Project Facts
- 2026-06-21: Project name is HEAT4YAFEAT (H4YF)
- 2026-06-21: Purpose is Brand Establishment and eCommerce
- 2026-06-21: GitHub repo is `ubiquitousautomation/H4YF`
- 2026-06-21: Owner email is ubiquitousautomation@gmail.com
- 2026-06-21: Primary dev agent is Claude via Claude Code (remote web session)
- 2026-06-21: Gemini accesses context files via Google Drive folder `H4YF/ai-context`

## Architecture Decisions
- 2026-06-21: AI context files live in `ai-context/` (git-tracked + Drive-synced)
- 2026-06-21: Sync tool is rclone with remote named `gdrive`
- 2026-06-21: Claude auto-pushes to Drive on session Stop via `.claude/settings.json` hook
- 2026-06-21: `push` uses `rclone copy` (non-destructive); `fullsync` uses `rclone sync` (destructive mirror — explicit only)
- 2026-06-21: Session logs tracked in git (not Drive-only) so Claude can read Gemini's history after pull
- 2026-06-21: Conflict resolution — sequential work assumed; `drive-sync.sh status` to inspect; human decides on true conflicts

## Key Conventions
- 2026-06-21: Branches follow pattern `claude/<feature>-<id>` for Claude Code branches
- 2026-06-21: `CLAUDE.md` is Claude's harness entrypoint; `GEMINI.md` is Gemini's
- 2026-06-21: Stop hook runs from project root — no absolute paths in `.claude/settings.json`
- 2026-06-21: All script invocations in docs use `bash ./scripts/...` form for cross-shell compatibility

## Environment & Tooling
- 2026-06-21: Owner machine is Windows 11 Home, VS Code with PowerShell as default terminal
- 2026-06-21: Git Bash is available but winget-installed rclone shim fails there (Permission denied on NTFS symlink)
- 2026-06-21: rclone v1.74.3 installed via winget on Windows; use PowerShell to run it
- 2026-06-21: rclone authorize port 53682 can get stuck — fix: `Stop-Process -Name rclone -Force` then retry
- 2026-06-21: Headless rclone OAuth flow: run `rclone authorize "drive"` locally → copy JSON token → paste into container with `rclone config create gdrive drive scope drive token '<json>'`
- 2026-06-21: `rclone bisync` requires `--first-run` on first invocation — drive-sync.sh auto-detects this

## People & Contacts
_(add as discovered)_

## External Services & Credentials
- Google Drive: used for Gemini context sync; rclone remote name `gdrive`; auth via OAuth (never log tokens here)
