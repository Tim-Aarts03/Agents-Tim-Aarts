# Agent Registry

Overview of all sub-agents. Claude Code (the manager) routes work to them.
Definitions live in `.claude/agents/`; archived agents live in `archive/`.

## Active

| Agent | Domain | Task | Tools | Status |
|---|---|---|---|---|
| `career-job-scout` | Career | Weekly (Friday) top 1–5 job vacancies; learns from Tim's 1–5 ratings (role, plus optional separate organisation rating) | `tools/job_scoring.py`, `tools/preference_learning.py`, `tools/applications_log.py` | active |
| `career-cover-letter-writer` | Career | Cover letters (recipient's language) for vacancies Tim selects; manager exports approved letters to Word | `tools/letter_checks.py`, `tools/applications_log.py`, `tools/letter_docx.py` | active |
| `mail-promo-writer` | Mail | Weekly 1–3 sentence pitch for the bootcamp promotion mail | `tools/bootcamp_mail.py` (log) | training |
| `mail-sender` (Python tool, no LLM) | Mail | Sends ONE approved weekly promotion mail via Apple Mail; send-only, allowlist, approval hash, max 1 per group per session | `tools/mail_sender.py` | active |
| `bootcamp-form-cleaner` (Google Apps Script, no LLM) | Mail | Tuesday 20:00: mails the sign-ups to Tim as archive, then clears the fixed form | `tools/google_apps_script/clear_bootcamp_responses.gs` (runs in Tim's Google account) | waiting for Tim to install |
| `bootcamp-reminder` (Google Apps Script, no LLM) | Mail | Monday ~12:45: reminder with weather advice to all sign-ups (BCC); phase 1 Gmail draft for Tim | `tools/google_apps_script/bootcamp_reminder.gs` (runs in Tim's Google account) | waiting for Tim to install |
| `finance-weekly-bookkeeper` | Finance | Books Tim's Wednesday update (sessions, expenses, invoices, payments) into the monthly ledger; builds the monthly Excel in Tim's layout + year overview; flags overdue invoices and KOR status | `tools/bookkeeping.py`, `tools/bookkeeping_xlsx.py` | training |
| `qa-fact-checker` | QA | Checks every output against `/knowledge` | `tools/letter_checks.py` | active |

## Mail workflow (bootcamp, training phase until ~2 Dec 2026)
- **Wednesday 07:00 promotion mail:** `mail-promo-writer` → Tim picks a pitch (+ gives the new form link) → `tools/bootcamp_mail.py promo` per group → `qa-fact-checker` → `tools/mail_sender.py preview` → Tim approves this exact mail → `tools/mail_sender.py send --approved-hash` (logs automatically).
- **Monday ~12:45 reminder:** Apps Script `bootcamp_reminder.gs` in Tim's form makes a Gmail draft (BCC sign-ups, weather advice) → Tim sends. Text kept identical to `tools/bootcamp_mail.py reminder` by a test.
- **Automatic (phase 1, from 25 Nov 2026):** scheduled task `bootcamp-promo-wednesday` (Wed ~06:40, Mac app must be open) runs `tools/bootcamp_weekly.py check` → `mail-promo-writer` → `compose` → `qa-fact-checker` → `mail_sender draft`. Never sends. One fixed sign-up form since 19 Nov 2026 (`session: fixed`); responses must be cleared after each Tuesday session.
- After two error-free weeks: propose automatic sending (needs a CLAUDE.md change approved by Tim).

## Bookkeeping workflow (from 19 Nov 2026)
- **Wednesday, on Tim's message** (no scheduled run): Tim says what happened and what he spent → `finance-weekly-bookkeeper` → `tools.bookkeeping add` per entry → `build` (Excel in `Boekhouding/Maandelijkse administratie/`) → `report` (`output/finance/week_<date>.md`) → manager reports in Dutch, with questions for anything not booked.
- Source of truth: `Boekhouding/data/<YYYY-MM>.json` (git-ignored); config in `knowledge/private_bookkeeping.json`. KOR monitoring is part of the tool (no separate agent).

## Planned

| Agent | Domain | Phase |
|---|---|---|
| `sales-quote-writer` | Sales | 2 |
| Bootcamp sign-up website (one fixed link, max 12, attendance) | Mail | 2b |
| `finance-invoice-writer` | Finance | 3 |
| `finance-income-tax-preparer` | Finance | 3 |

## Archived

_None yet._
