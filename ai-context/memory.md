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

## Key Conventions
- 2026-06-21: Branches follow pattern `claude/<feature>-<id>` for Claude Code branches
- 2026-06-21: `CLAUDE.md` is Claude's harness entrypoint; `GEMINI.md` is Gemini's

## People & Contacts
_(add as discovered)_

## External Services & Credentials
_(add service names here — never log secrets in this file)_
