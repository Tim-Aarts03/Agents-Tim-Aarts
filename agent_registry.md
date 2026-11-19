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
| `qa-fact-checker` | QA | Checks every output against `/knowledge` | `tools/letter_checks.py` | active |

## Mail workflow (bootcamp, training phase until ~2 Dec 2026)
- **Wednesday 07:00 promotion mail:** `mail-promo-writer` → Tim picks a pitch (+ gives the new form link) → `tools/bootcamp_mail.py promo` per group → `qa-fact-checker` → `tools/mail_sender.py preview` → Tim approves this exact mail → `tools/mail_sender.py send --approved-hash` (logs automatically).
- **Monday ~13:00 reminder:** `tools/bootcamp_mail.py reminder` (weather via `tools/bootcamp_weather.py`) to the people who signed up → `qa-fact-checker` → draft → Tim sends → `log_mail`.
- **Automatic (phase 1, from 25 Nov 2026):** scheduled task `bootcamp-promo-wednesday` (Wed ~06:40, Mac app must be open) runs `tools/bootcamp_weekly.py check` → `mail-promo-writer` → `compose` → `qa-fact-checker` → `mail_sender draft`. Never sends. One fixed sign-up form since 19 Nov 2026 (`session: fixed`); responses must be cleared after each Tuesday session.
- After two error-free weeks: propose automatic sending (needs a CLAUDE.md change approved by Tim).

## Planned

| Agent | Domain | Phase |
|---|---|---|
| `sales-quote-writer` | Sales | 2 |
| Bootcamp sign-up website (one fixed link, max 12, attendance) | Mail | 2b |
| `finance-invoice-writer` | Finance | 3 |
| `finance-transaction-processor` | Finance | 3 |
| `finance-kor-monitor` | Finance | 3 |
| `finance-income-tax-preparer` | Finance | 3 |

## Archived

_None yet._
