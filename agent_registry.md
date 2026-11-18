# Agent Registry

Overview of all sub-agents. Claude Code (the manager) routes work to them.
Definitions live in `.claude/agents/`; archived agents live in `archive/`.

## Active

| Agent | Domain | Task | Tools | Status |
|---|---|---|---|---|
| `career-job-scout` | Career | Weekly (Friday) top 1–5 job vacancies; learns from Tim's 1–5 ratings | `tools/job_scoring.py`, `tools/preference_learning.py`, `tools/applications_log.py` | active |
| `career-cover-letter-writer` | Career | Dutch cover letters for vacancies Tim selects | `tools/letter_checks.py`, `tools/applications_log.py` | active |
| `mail-promo-writer` | Mail | Weekly 1–3 sentence pitch for the bootcamp promotion mail | `tools/bootcamp_mail.py` (log) | training |
| `qa-fact-checker` | QA | Checks every output against `/knowledge` | `tools/letter_checks.py` | active |

## Mail workflow (bootcamp, training phase until ~2 Dec 2026)
- **Wednesday 07:00 promotion mail:** `mail-promo-writer` → Tim picks a pitch (+ gives the new form link) → `tools/bootcamp_mail.py promo` per group → `qa-fact-checker` → draft in Tim's Gmail → Tim sends → `log_mail`.
- **Monday ~13:00 reminder:** `tools/bootcamp_mail.py reminder` (weather via `tools/bootcamp_weather.py`) to the people who signed up → `qa-fact-checker` → draft → Tim sends → `log_mail`.
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
