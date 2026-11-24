# Agent Registry

Overview of all sub-agents. Claude Code (the manager) routes work to them.
Definitions live in `.claude/agents/`; archived agents live in `archive/`.

## Active

| Agent | Domain | Task | Tools | Status |
|---|---|---|---|---|
| `career-job-scout` | Career | Weekly (Friday) top 1–5 job vacancies; learns from Tim's 1–5 ratings (role, plus optional separate organisation rating) | `tools/job_scoring.py`, `tools/preference_learning.py`, `tools/applications_log.py` | active |
| `career-event-scout` | Career | Weekly (Friday) top 1–5 networking events in the next six weeks; goal one event per month; learns from Tim's ratings before and after an event; never registers | `tools/events.py` (scoring, log `logs/events.csv`, learning, month check) | training |
| `career-cover-letter-writer` | Career | Cover letters (recipient's language) for vacancies Tim selects; manager exports approved letters to Word | `tools/letter_checks.py`, `tools/applications_log.py`, `tools/letter_docx.py` | active |
| `career-cv-advisor` | Career | Per selected vacancy: CV tailoring advice with exact text changes; manager applies approved changes to a copy of Tim's Canva CV and exports a PDF | Canva connector (manager), `knowledge/private_cv_en.md` | trial |
| `mail-promo-writer` | Mail | Weekly 1–3 sentence pitch for the bootcamp promotion mail | `tools/bootcamp_mail.py` (log) | training |
| `mail-sender` (Python tool, no LLM) | Mail | Sends ONE approved weekly promotion mail via Apple Mail; send-only, allowlist, approval hash, max 1 per group per session | `tools/mail_sender.py` | active |
| `bootcamp-form-cleaner` (Google Apps Script, no LLM) | Mail | Tuesday 20:00: mails the sign-ups to Tim as archive, then clears the fixed form | `tools/google_apps_script/clear_bootcamp_responses.gs` (runs in Tim's Google account) | active (first run OK 2026-11-23) |
| `bootcamp-reminder` (Google Apps Script, no LLM) | Mail | Monday ~12:45: reminder with weather advice to all sign-ups (BCC); phase 1 Gmail draft for Tim | `tools/google_apps_script/bootcamp_reminder.gs` (runs in Tim's Google account) | active (first run OK 2026-11-23) |
| `finance-weekly-bookkeeper` | Finance | Books Tim's Wednesday update (sessions, expenses, invoices, payments) into the monthly ledger; builds the monthly Excel in Tim's layout + year overview; flags overdue invoices and KOR status | `tools/bookkeeping.py`, `tools/bookkeeping_xlsx.py` | training |
| `finance-invoice-writer` | Finance | Drafts a sales invoice (Markdown + PDF in Tim's 001 layout) from unbilled sessions; manager finalizes after Tim's approval (PDF to `01 Verkoop Facturen/`, invoice booked) | `tools/invoice.py` | training |
| `invest-crypto-analyst` | Invest | Thursday analysis of the paper-trading market watch (pot vs market, trades, health), max 1 rule proposal tested on unseen data | `tools/crypto.py` (report, backtest) | training |
| `crypto-market-watch` (Python, launchd, no LLM) | Invest | Hourly: BTC/ETH prices from the public Binance API, active rule, paper trades in a virtual €100 pot; alerts only when no prices for >24h | `tools/crypto.py tick` | active (from 23 Nov 2026) |
| `site-builder` (Python tool, no LLM) | Sales | Builds the one-page T.A Vitality website for employers (weekly movement sessions); phone/KvK filled from `knowledge/private_*`, output `output/site/index.html` (not online yet) | `tools/site_build.py`, `site/` | draft (colours and form/booking links pending) |
| `qa-fact-checker` | QA | Checks every output against `/knowledge` | `tools/letter_checks.py` | active |

## Mail workflow (bootcamp, training phase until ~2 Dec 2026)
- **Wednesday 07:00 promotion mail:** `mail-promo-writer` → Tim picks a pitch (+ gives the new form link) → `tools/bootcamp_mail.py promo` per group → `qa-fact-checker` → `tools/mail_sender.py preview` → Tim approves this exact mail → `tools/mail_sender.py send --approved-hash` (logs automatically).
- **Monday ~12:45 reminder:** Apps Script `bootcamp_reminder.gs` in Tim's form makes a Gmail draft (BCC sign-ups, weather advice) → Tim sends. Text kept identical to `tools/bootcamp_mail.py reminder` by a test.
- **Automatic (phase 1, from 25 Nov 2026):** scheduled task `bootcamp-promo-wednesday` (Wed ~06:40, Mac app must be open) runs `tools/bootcamp_weekly.py check` → `mail-promo-writer` → `compose` → `qa-fact-checker` → `mail_sender draft`. Never sends. One fixed sign-up form since 19 Nov 2026 (`session: fixed`); responses must be cleared after each Tuesday session.
- After two error-free weeks: propose automatic sending (needs a CLAUDE.md change approved by Tim).

## Bookkeeping workflow (from 19 Nov 2026)
- **Wednesday, on Tim's message** (no scheduled run): Tim says what happened and what he spent → `finance-weekly-bookkeeper` → `tools.bookkeeping add` per entry → `build` (Excel in `Boekhouding/Maandelijkse administratie/`) → `report` (`output/finance/week_<date>.md`) → manager reports in Dutch, with questions for anything not booked.
- Source of truth: `Boekhouding/data/<YYYY-MM>.json` (git-ignored); config in `knowledge/private_bookkeeping.json`. KOR monitoring is part of the tool (no separate agent).

## Invoice workflow (from 19 Nov 2026)
- Tim asks for an invoice → `finance-invoice-writer` runs `tools.invoice draft` → `qa-fact-checker` on the Markdown → Tim approves the PDF → manager runs `tools.invoice finalize <nr> --approved` → Tim sends it himself; payment is booked later via the bookkeeper.
- Contract Sint Jacob: invoice afterwards, after 15 Dec 2026 (the tool warns when invoicing earlier).

## Invest workflow (paper trading only, from 23 Nov 2026)
- Never real money, exchange accounts, wallets or API keys (hard rule in CLAUDE.md §6).
- launchd job `com.agents.crypto-watch` runs `tools.crypto tick` hourly (Mac must be awake; missed hours are skipped, not traded afterwards). Disable with `.venv/bin/python -m tools.crypto uninstall-watch` (plist kept as `.disabled`).
- Thursday 09:00 scheduled task `invest-crypto-thursday` → `invest-crypto-analyst` → `output/invest/crypto_week_<date>.md` → Max reports. Rule changes only via `tools.crypto activate <rule> --reason ... --approved` after Tim's yes, and at least 28 days after the previous switch (enforced). Backtest covers 4 years, hourly and daily (`d_*`) rules, with return and largest drop.
- Data: `logs/crypto_state.json`, `logs/crypto_paper_trades.csv`, `logs/crypto_equity.csv`, `logs/crypto_history_*.csv` (git-ignored). Rules + rule history: `knowledge/crypto_rules.json` (in git).

## Planned

| Agent | Domain | Phase |
|---|---|---|
| `sales-quote-writer` | Sales | 2 |
| Bootcamp sign-up website (one fixed link, max 12, attendance) | Mail | 2b |
| `finance-income-tax-preparer` | Finance | 3 |

## Archived

_None yet._
