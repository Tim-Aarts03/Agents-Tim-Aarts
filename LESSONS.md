# LESSONS.md — Lessons Learned

Shared logbook of Tim and Claude. Goal: never make the same mistake twice and
remember decisions and preferences across sessions.

**How we use it**
- Claude adds an entry after every feature, bug fix or feedback moment.
- Tim may add or correct entries at any time.
- Before starting a task, Claude reads this file.
- Lessons that must always apply are proposed for `CLAUDE.md`.

**Format per entry**
```
### YYYY-MM-DD — short title
- Situation: what happened
- Lesson: what we learned
- Action: what changed (file, rule, agent)
```

---

### 2026-11-16 — Architecture choice C
- Situation: choice between Claude Code as manager (A), a standalone Python orchestrator (B) or a mix (C).
- Lesson: Tim is a beginner and has no income yet; cheapest and safest wins.
- Action: Claude Code manages sub-agents in `.claude/agents/`; deterministic Python tools in `/tools`. No standalone API agents unless Tim asks.

### 2026-11-16 — Sub-agents live in `.claude/agents/`
- Situation: CLAUDE.md prescribed `/agents`, but Claude Code only discovers sub-agents in `.claude/agents/`.
- Action: CLAUDE.md section 4 updated; naming `<domain>-<task>.md`; `archive/` and `agent_registry.md` added.

### 2026-11-16 — Source documents contained contradictions
- Situation: age (22 vs 24), language levels and Sint Jacob dates differed between CVs and letters.
- Lesson: source documents are not automatically correct; Tim confirms facts once, then `knowledge/profile.md` is the single source of truth.
- Action: corrected profile; `qa-fact-checker` checks every output against it.

### 2026-11-16 — LinkedIn may not be scraped
- Situation: LinkedIn's terms forbid automated searching.
- Action: job-scout searches public job sites and employer career pages; Tim forwards LinkedIn alerts manually.

### 2026-11-16 — VAT: KOR applies
- Situation: T.A Vitality is a sole proprietorship (eenmanszaak) using the KOR.
- Lesson: no VAT is charged and no VAT return is filed; instead monitor the €20,000 turnover threshold.
- Action: planned `finance-kor-monitor` instead of a VAT-return agent (phase 3).

### Tim's preferences
- Communication in Dutch, direct, no filler. Code in English.
- Controls agents by chatting (no fixed commands needed).
- Friday: top 1–5 vacancies; Tim picks numbers; letters per pick; Tim approves and sends the letters.
- Agents are archived, never deleted.
- No specific banned phrases in letters (yet); letters improve through feedback and outcomes.

### 2026-11-16 — Application log is tracked in git
- Situation: Tim works in ephemeral cloud sessions; a gitignored `logs/` folder would be lost each session, breaking the learning loop.
- Lesson: data needed for learning across sessions must live in git, as long as it contains no sensitive data.
- Action: `.gitignore` exception for `logs/applications.csv` (approved by Tim); noted in CLAUDE.md section 6.
