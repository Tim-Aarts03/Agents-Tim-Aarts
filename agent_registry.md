# Agent Registry

Overview of all sub-agents. Claude Code (the manager) routes work to them.
Definitions live in `.claude/agents/`; archived agents live in `archive/`.

## Active

| Agent | Domain | Task | Tools | Status |
|---|---|---|---|---|
| `career-job-scout` | Career | Weekly (Friday) top 1–5 job vacancies; learns from Tim's 1–5 ratings | `tools/job_scoring.py`, `tools/preference_learning.py`, `tools/applications_log.py` | active |
| `career-cover-letter-writer` | Career | Dutch cover letters for vacancies Tim selects | `tools/letter_checks.py`, `tools/applications_log.py` | active |
| `qa-fact-checker` | QA | Checks every output against `/knowledge` | `tools/letter_checks.py` | active |

## Planned

| Agent | Domain | Phase |
|---|---|---|
| `sales-quote-writer` | Sales | 2 |
| `finance-invoice-writer` | Finance | 3 |
| `finance-transaction-processor` | Finance | 3 |
| `finance-kor-monitor` | Finance | 3 |
| `finance-income-tax-preparer` | Finance | 3 |

## Archived

_None yet._
