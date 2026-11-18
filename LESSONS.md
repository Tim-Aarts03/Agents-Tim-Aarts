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

### Tim's preferences (updated 2026-11-18, from the CLAUDE.md interview)
- Answers: 1–2 sentences, then what Tim must do; fixed closing block (Gedaan / Jij moet / Volgende stap).
- Open questions, not multiple choice. Technical explanation only for decisions Tim must make.
- Claude may commit and push on its own once tests pass; CLAUDE.md and profile.md changes need a plan + approval.
- Plan + approval for: new agents/tools, decisions on Tim's behalf, money, contacting other people (sending only with explicit approval per send).
- Never: spend money, share personal data, act outside the instructions or outside the project folder. No response from Tim = wait.
- Works only on the Mac from now on. Friday: the top 5 should be ready when Tim opens Claude, followed by an evaluation (max 3 improvements).
- Max 3 agents in parallel; warn only when a task costs money or uses unusually much.
- Improvement suggestions only when they really add value.
- Tim is a beginner with AI: teach him short, practical tips on working with agents.
- Priority after career: mail agents (weekly use), then bookkeeping, then quotes.
- Goal in 10 weeks: career, mail and bookkeeping agent groups working under Claude; Tim only talks to Claude.
- Earlier: controls agents by chatting; agents are archived, never deleted; no banned phrases yet in letters.

### 2026-11-16 — Application log is tracked in git
- Situation: Tim works in ephemeral cloud sessions; a gitignored `logs/` folder would be lost each session, breaking the learning loop.
- Lesson: data needed for learning across sessions must live in git, as long as it contains no sensitive data.
- Action: `.gitignore` exception for `logs/applications.csv` (approved by Tim); noted in CLAUDE.md section 6.

### 2026-11-17 — First job-scout trial run: network blocked
- Situation: the cloud environment only allows package registries; every vacancy page failed (ENOTFOUND). Creating or updating the environment via Claude's tools was rejected by the service.
- Lesson: the scout correctly refused to rank vacancies from search snippets. Job sites must be allowed in the environment settings (done by Tim) before a web run.
- Action: until then, Tim pastes vacancy texts/links; scout should test one fetch first and stop early with a clear message.

### 2026-11-17 — Scoring model gaps found in trial run
- Situation: real input (LinkedIn post, Upfront) exposed gaps: no `unknown` location, `hours: unknown` scores the same as full-time, domain ambiguity (role vs organisation), subjective `strong_learning_environment`, binary `requirements_risk`, no "still open" check.
- Action (approved 2026-11-17): `location` is now derived by the tool from `city` + `knowledge/preferred_places.json`; `unknown` location; unknown hours < full-time; domain = role, not organisation; `learning_evidence` only from explicit text; graded `requirement_gaps`; network check + search-only mode in the scout.

### 2026-11-17 — Learning from Tim's ratings
- Situation: Tim wants the scout to learn which vacancies he finds interesting, also from his earlier applications.
- Lesson: an attractive company does not compensate for an unsuitable role (Upfront, rated 2). Tim wants a job (no internship; traineeship welcome) that looks strong on the CV, builds a network and offers many learning situations.
- Action: Tim rates every proposed vacancy 1–5; `tools/preference_learning.py` turns average ratings per feature (domain, role type, org type, employment type) into a bonus of max ±10, active after 3 ratings per feature. Log seeded with Cruyff Foundation (5), Kenniscentrum Specialist jeugd (5), Ajax internship (4), Upfront (2). Internships are excluded by the scoring tool.

### 2026-11-18 — Profile rebuilt from interview
- Situation: CV facts were outdated or inflated (Spanish "intermediate" is really A1–A2; "eerste divisie" at HFC is wrong; football ended through travel, then a cruciate ligament injury).
- Lesson: Tim's own CV overstates some things; letters must use `profile.md` only, never the CV PDFs.
- Action: `knowledge/profile.md` rewritten; references in `knowledge/private_references.md` (not in git).

### 2026-11-18 — Job preferences sharpened
- Tim wants to lead, set up projects and make policy; never buurtsportcoach or teaching sports lessons. Dream employers: Upfront, Adidas, UEFA Foundation. Organisations must do good for the world (not FIFA, not Red Bull).
- Action: `knowledge/job_filters.json` (excluded organisations and role types, preferred role types +5); scoring tool and scout updated.

### 2026-11-18 — Standing mandate for CLAUDE.md and profile.md
- Tim: "If I ask you to change CLAUDE.md or profile.md, just do it right in one go; I won't approve drafts."
- Action: CLAUDE.md §2 updated. Only changes Claude proposes itself still need approval.

### 2026-11-18 — First full job-scout run (local, network OK)
- Situation: 9 candidates, top 5 proposed; ~45 web calls. Indeed single job pages return 401, werkzoeken 403; career-page URLs had to be guessed (404 looked like a network failure). The fetch model invented one Indeed URL (dropped by the scout).
- Lesson: links from fetch summaries are not proof; unverified vacancies can outrank verified ones; QA caught overstated profile claims (Tim *coordinated* La Matanza sports lessons, he did not teach them).
- Open proposals: real career-page URLs in `knowledge/job_sources.md`; penalty or separate list for `verified: false`; hours threshold (≥32 = full-time); `--no-log-exclusion` flag for QA re-scoring; remove `domain:sports_brand` from the Upfront seed row.

### 2026-11-18 — Tim's ratings expose role vs. company conflict
- Situation: Tim rated ASICS graduate roles "company + programme 5, role 3 (merchandise) / 1 (social media)". One rating per vacancy applies to all features, so `org_type:commercial_brand` and `domain:sports_brand` are now active at 2.0 and will push sports brands down, the opposite of what Tim wants. The Upfront seed row (wrongly tagged `domain:sports_brand`) adds to this.
- Lesson: Tim judges the organisation and the role separately; the learning model must too.
- Proposal (needs Tim's OK): separate role rating and organisation rating, and fix the Upfront tag.

### 2026-11-18 — GitHub Desktop stashed uncommitted work
- Situation: pulling in GitHub Desktop put Claude's uncommitted changes in a stash ("!!GitHub_Desktop<main>"); the log looked empty.
- Action: restored with `git stash apply` (stash kept as backup). Commit finished work promptly, and run `git pull` at session start (CLAUDE.md §3).

### 2026-11-18 — Training round with fictional vacancies
- Situation: Tim wants to train the scout on his taste before real runs.
- Action: 20 varied fictional vacancies logged with status `training` (URLs `https://training.invalid/vNN`); Tim rates them 1–5 with reasons; ratings feed `tools/preference_learning.py` like real ratings. Scores are not shown to Tim to avoid anchoring.

### 2026-11-18 — What the 20 training ratings taught us
- Rated 5: traineeship with rotation (3), community & impact at a big brand (7), international youth foundation abroad (9), fundraising/partnerships at a youth foundation (14), traineeship consultancy for government (17), national sport policy (19).
- Pattern: big impact and scale + a strong network + learning from experienced people. Fundraising/partnership "sales" for a good cause is great; selling a product (sports nutrition) is not.
- Low: club management (1), event logistics (2), sports nutrition sales (2), research requiring a master's (2 now, 5 later), apps and start-ups not his own (-1 each by Tim's own rule).
- Feasibility lowers ratings (master's, years of experience): Tim wants a traineeship first, then policy roles.
- Hours and distance matter for average roles (Zaandam, 32 h), not for dream roles (40 h and abroad fine).
- Excluded organisation: De Atleetfabriek (Tim's earlier internship).

### 2026-11-18 — Scoring rebalanced after training round
- Situation: with the old weights, local roles near home (rated 3) ranked above Tim's 5s; learned bonuses alone could not fix it (leave-one-out Spearman ~0.33 for every learning weight tried).
- Lesson: fixed weights encoded my assumptions (domain and distance), not Tim's taste (scale of impact, network). Validate weights against Tim's ratings before trusting them.
- Action: new `impact_scale` field (international 20 / national 12 / unknown 5 / local 0); domain, location and hours points lowered; abroad not penalised for international impact; -10 for start-ups that are not Tim's own and -10 for app products; new role type `partnerships_fundraising` (preferred). Leave-one-out Spearman now 0.62; all four top-ranked training vacancies are rated 5.
- Known gap: one-off role types (e.g. fundraising, rated 5) stay low until rated more often.

### 2026-11-18 — Mail agents for the bootcamp (plan approved)
- Tim mails a weekly promotion (Wednesday 07:00) to Hof van Jacob (via his mother) and a few Jacob Kliniek addresses, and a standard reminder on Monday ~13:00 to people who signed up. Only the 1–3 sentence pitch changes each week.
- Goal: automatic creation and sending within ~2 weeks, after training on drafts. Tim fears "weird mails to everyone": QA before every draft.
- Action: `knowledge/bootcamp.md`, `tools/bootcamp_mail.py` (composition, dates, log), `tools/bootcamp_weather.py` (below 12 °C warm clothing; rain → covered balcony of team 2), agent `mail-promo-writer`. Participant names from examples anonymised in git.
- Open: Gmail draft route on the Mac (Gmail connector or Apple Mail), whether Form responses land in a Google Sheet, recipient addresses (`knowledge/private_mail_recipients.json`).
