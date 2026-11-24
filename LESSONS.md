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
- Tim values honest feedback (2026-11-19): say plainly when something is not needed yet or when a different approach is better, even if he asked for something else.
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

### 2026-11-18 — First Friday run with rebalanced scoring
- Situation: only 5 candidates (all verified), no traineeships, top score 42. ~40 web calls; broad WebSearch mostly returns expired vacancies.
- Lesson: a good-cause fundraising role (Jeugdfonds, type Tim rated 5 in training) scored 28, below admin roles at UEFA: `domains: []` gives 0 domain points and `partnerships_fundraising` is not yet learned. The scout also wrote a self-computed "deadline in 6 days" (fixed); deadlines must be stated as dates only.
- Friday evaluation (proposals, need Tim's OK): (1) give fundraising/policy roles at foundations/government a domain or role-fit bonus; (2) fixed source URLs in `job_sources.md`, incl. uefa.com/insideuefa/careers and gehandicaptensport.nl; (3) traineeship providers list with recruiting months + LinkedIn alerts.

### 2026-11-18 — Ratings, letters and Friday-evaluation fixes
- Tim's ratings: Mulier onderzoeksassistent 5 (selected), UEFA Planning & Services Coordinator selected (no number yet), UEFA Club Competitions skipped (1–3 yrs data experience not feasible), Jeugdfonds fondsenwerver 1 (5 yrs experience required: a feasibility 1, not a dislike of fundraising), Happy2Move planner "prima" (no number yet).
- Lesson: Tim often answers without a number; ask for the missing numbers instead of guessing. Infeasibility drives ratings down, so a low rating on a preferred role type can be about requirements, not the role.
- Action (approved by Tim): `good_cause_role_bonus` (+10) for preferred roles at foundations/government (`knowledge/job_filters.json`); `knowledge/job_sources.md` rewritten with checked career-page URLs, a traineeship-provider list (recruitment months only when a page states them) and a "not working" list.
- Letters: writer used the recipient's language (English for UEFA). `tools.letter_checks` counts the "Notities voor Tim" below `---`, so every letter fails the 400-word check; Dutch-only typo and age checks do not work on English letters. Proposed fix needs Tim's OK.

### 2026-11-18 — Mail agents for the bootcamp (plan approved)
- Tim mails a weekly promotion (Wednesday 07:00) to Hof van Jacob (via his mother) and a few Jacob Kliniek addresses, and a standard reminder on Monday ~13:00 to people who signed up. Only the 1–3 sentence pitch changes each week.
- Goal: automatic creation and sending within ~2 weeks, after training on drafts. Tim fears "weird mails to everyone": QA before every draft.
- Action: `knowledge/bootcamp.md`, `tools/bootcamp_mail.py` (composition, dates, log), `tools/bootcamp_weather.py` (below 12 °C warm clothing; rain → covered balcony of team 2), agent `mail-promo-writer`. Participant names from examples anonymised in git.
- Open: Gmail draft route on the Mac (Gmail connector or Apple Mail), whether Form responses land in a Google Sheet, recipient addresses (`knowledge/private_mail_recipients.json`).

### 2026-11-18 — Bootcamp mail: recipient set, pitch training round
- Situation: Hof van Jacob mail goes to one contact person who forwards it (Tim has no access to internal Sint Jacob mailing lists); address stored in `knowledge/private_mail_recipients.json`. Before drafting real mails Tim wants to learn his taste first, like the job-scout training round.
- Action: `mail-promo-writer` wrote 20 pitches spread over length, tone, hook and emoji (`output/mail/pitch_training_2026-11-18.md`); Tim rates them 1–5. Manager fixed two small errors before showing them ("zeker jouw plekje", "🔥!").
- Open: where the ratings live (the mail log is git-ignored); this week's promotion mail waits until after the ratings.

### 2026-11-18 — UEFA letter finalised
- Tim is willing to relocate to Switzerland or France for UEFA, and would drop the T.A Vitality bootcamp for this job. Added "I am prepared to relocate to the Nyon area." to the letter (stated by Tim in chat; not yet in `profile.md`).

### 2026-11-18 — Approved letters go to Word automatically
- Tim wants a ready-to-send Word file as soon as he is satisfied with a letter.
- Action: `tools/letter_docx.py` exports the letter part (above `---`) to `output/career/letter_<org>_<date>.docx` (A4, Calibri 11); step added to the career workflow in CLAUDE.md §6. Give Tim the .docx path and the vacancy link together.

### 2026-11-18 — First applications sent
- Tim applied to UEFA Football Planning & Services Coordinator (rated 4: fits the gap year, moving abroad is fine, unsure about the role, very competitive) and Mulier Instituut onderzoeksassistent (rated 5). Happy2Move planner letter is ready but not sent.
- Happy2Move planner rated 3 (mainly administrative); letter written and exported to Word on Tim's request.
- Next: record outcomes (invited/rejected/no response) in `logs/applications.csv` and `knowledge/letter_style.md` when Tim hears back.

### 2026-11-18 — What the 20 pitch ratings taught us
- Rated 5: clearing your head after work (2), T-shirt progress (3), bring a colleague (11, 12), energy boost (14), dark November turned into fun (18). Rated 1–2: record of 10, limited places, sweat.
- Pattern: 2–3 sentences, emotion + call to action + 1–3 fitting emoji. One-liners feel bare. Topical hooks (Black Friday) are a plus. Never mention who pays or the weather.
- Tim rated by voice and sometimes without a number (11 inferred as 5 from "topper"; 13 and 16 missing).
- Action: style rules in `knowledge/bootcamp.md` (read by `mail-promo-writer`); ratings in `logs/pitch_ratings.csv` (local, git-ignored).
- Follow-up 2026-11-18: Tim corrected 11 to 4 (not the inferred 5), 13 = 3, 16 = 2. Inferring a number from words was wrong once: always ask.
- First real promotion mail (24 Nov) drafted with pitch 18, QA PASS; Tim sends it himself (no Gmail connector yet).

### 2026-11-18 — Sending the promotion mail after Tim's approval (approved plan)
- Tim's strict rules: the sender may do nothing else in his mail: no reading, searching or other mails; only the weekly promotion mail to the allowed account.
- Action: `tools/mail_sender.py` (Apple Mail via AppleScript, send-only). Refuses on: recipient not in `knowledge/private_mail_recipients.json`, non-promotion subject, content changed after Tim's approval (hash from `preview`), second send for the same session. `.claude/settings.json` denies Claude raw `osascript` and reading `~/Library/Mail`. Reminders to sign-ups are NOT covered yet (needs a new plan).
- Flow: preview → Tim says "verstuur" → send with that preview's hash. Approval per send stays.
- 2026-11-18: Tim chose "put it in Concepten" instead of sending. Added `draft` mode (AppleScript `save msg`, logged as `promo_draft`, does not block a later send). First draft for 24 Nov saved in Apple Mail.

### 2026-11-18 — Weekly promotion mail automated (phase 1, approved)
- Tim sent the first draft himself; goal is fully automatic weekly mails.
- Action: `tools/bootcamp_weekly.py` (check: link valid for the coming Tuesday, recipient present, no mail yet this session; compose: draft JSON + hash) and scheduled task `bootcamp-promo-wednesday` (Wed 06:30, runs in Auto mode, drafts only). Sign-up link lives in `knowledge/bootcamp_form.json` (`session` = Tuesday ISO date or `fixed`).
- Open: Tim to decide on one fixed form; phase 2 (auto-send) after two error-free weeks needs a CLAUDE.md change.

### 2026-11-19 — Friday run automated
- Tim wants the top 5 vacancies every Friday by 09:00 without doing anything himself; he only picks which ones to apply for.
- Action: local scheduled task `career-friday-run` (Claude app, Fridays 08:15 + a few minutes jitter, Auto mode). It pulls, runs `career-job-scout`, logs the vacancies, appends a Friday evaluation here, commits, tries to push and reports the top 5 in Dutch. It skips if today's vacancies file already exists (also avoids a double run via CLAUDE.md §3).
- Limits: runs only while the Claude app is open on Tim's Mac (otherwise on next launch); push fails without GitHub credentials in the terminal.

### 2026-11-19 — Evaluation week 1: role and organisation rated separately
- Situation: one rating per vacancy taught "sports brands are bad" from ASICS (company 5, roles 3 and 1); `org_type:commercial_brand` was at ~2.
- Action (approved by Tim): optional `org_rating` in `logs/applications.csv`; `org_type` and `impact_scale` learn from it when given, all other features from the role rating. ASICS org_rating 5 (Tim's own words); `domain:sports_brand` removed from the Upfront seed. `commercial_brand` is now 3.8. CLI: `rate <url> <role> --org <n> <reason>`.

### 2026-11-19 — Letter checks fixed
- Situation: notes below `---` were counted, so every letter failed the 400-word check; age and typo checks were Dutch-only.
- Action: `tools.letter_checks` checks only the part above `---`, detects nl/en, checks "23 years old"/"23-year-old" in English and skips Dutch typos there. All three existing letters now pass.

### 2026-11-19 — One fixed bootcamp sign-up form
- Tim now uses one fixed Google Form; `knowledge/bootcamp_form.json` set to `fixed`, so the Wednesday check no longer stops on an old link.
- Tim wants responses cleared every Tuesday. Claude has no access to Google Forms (and should not): approved a bound Google Apps Script in Tim's own form (`tools/google_apps_script/`), trigger Tuesday 20:00 Amsterdam. It archives responses to the Sheet "Bootcamp aanmeldingen archief" before `deleteAllResponses()`, and does nothing on other days. Tim installs it himself (Dutch step-by-step in the README).

### 2026-11-19 — Bookkeeping agent (plan approved)
- Situation: Tim kept monthly Excel files (7 tabs) plus a year overview by hand. He wants no scheduled run: on Wednesday he tells what happened and what he spent, and the books are updated.
- Lesson: Tim's "copy" in the project folder was a Finder alias, not a copy; check what a file really is before relying on it. Invoice 001 appears in both the September and October file (double entry); hand-made books need a check before being taken over.
- Action: `tools/bookkeeping.py` (JSON ledger per month, all arithmetic, checks, overdue invoices, KOR status) and `tools/bookkeeping_xlsx.py` (Excel in Tim's layout; never overwrites hand-made files); agent `finance-weekly-bookkeeper`. Data in `Boekhouding/` and `knowledge/private_bookkeeping.json`, both git-ignored. KOR monitoring folded into the tool instead of a separate agent.


### 2026-11-19 — Monday reminder via Apps Script (approved plan)
- Tim wants the Monday reminder sent automatically to everyone who signed up.
- Decision: the reminder runs as Apps Script in Tim's own form (`tools/google_apps_script/bootcamp_reminder.gs`, Monday ~12:45), so participant addresses never reach Claude or git. Same text and weather rules as `tools/bootcamp_mail.py`; `tests/test_apps_script_reminder.py` (Node) keeps both identical. Participants in BCC; at most one per Monday; nothing if nobody signed up.
- Phase 1: Gmail draft + a note to Tim; Tim sends. Phase 2 (`REMINDER_SEND_AUTOMATICALLY = true`) only after two error-free weeks and a CLAUDE.md change approved by Tim.

### 2026-11-19 — First bookkeeping update
- Tim: invoice 001 is unpaid but being handled; no reminders or questions about it. Sessions of 3, 10 and 17 Nov given; he did not give participant numbers.
- Lesson: Tim assumed sessions were already in the books; the agent only knows what Tim tells it. Participant numbers are optional, don't ask for them.
- Action: `participants` optional; invoice `follow_up` replaces the reminder suggestion. The agent still re-asked the invoice-001 date question from the setup log; that log line is now closed.


### 2026-11-19 — Apps Script asked for full Gmail access
- Situation: during install Google asked Tim for "everything you can do in Gmail" (read, delete, labels), because `GmailApp` always requires the full `mail.google.com` scope. Tim noticed and asked before accepting.
- Lesson: check which permissions a Google API call needs before handing Tim a script; least privilege also applies outside the project folder.
- Action: explicit `appsscript.json` with only `gmail.compose` (drafts + send), `forms.currentonly` and the other needed scopes; reminder uses the Gmail advanced service instead of `GmailApp`. Test fails if `GmailApp`/`MailApp` or the full Gmail scope ever returns. README tells Tim which text to expect on the consent screen.

### 2026-11-19 — Reminder dry run showed the wrong session date
- Situation: Tim's dry run on Thursday said "morgen (20 november)"; the script used "tomorrow" as the session date. Only correct on Mondays.
- Lesson: never derive a session date from "tomorrow"; always from the fixed weekday (Tuesday), like `next_tuesday` in Python. Test dry runs on other weekdays too.
- Action: `nextSession_()` = first Tuesday strictly after today (Amsterdam); Node test covers Monday, Thursday, Tuesday and summer time.

### 2026-11-19 — Tim's own November sheet is the layout standard
- Situation: Tim sent his own version of the November file (likely prepared in a chat elsewhere) with participants, five expenses (Claude Pro + reverse-charge VAT, cash yoga mats without receipt, Plus, Lidl gift) and his preferred layout.
- Lesson: Tim wants his familiar layout exactly: title row "owner | year | month", start/end times in hours, Cijfer column, assumptions directly under the table, colour code, "(voorlopig)" until the month is closed, short client name "Sint Jacob".
- Action: `tools/bookkeeping_xlsx.py` rewritten to his layout; free-text payment method and status, session rating, contract progress and session summary generated; data booked in the November ledger.
- Open: reverse-charge VAT means a VAT return although the KOR applies (earlier lesson said "no VAT return"); Tim checks this with an accountant.

### 2026-11-19 — Business name stays T.A Vitality
- Situation: Tim's sheet mentioned a new trade name; Claude adopted it in the bookkeeping. Tim: "Houd T.A Vitality aan", everything back.
- Lesson: never adopt a new business name (or other identity fact) from a document; confirm with Tim first.
- Action: config, November note and Excel files back to T.A Vitality.


### 2026-11-19 — Google permissions cut to the minimum (Tim: "remove all unnecessary permissions")
- Situation: the consent screen still asked for all spreadsheets (archive Sheet) and e-mail address access.
- Action: archive is now a mail to Tim himself (reuses `gmail.compose`; nothing is deleted if that mail fails); Tim's address comes from the Gmail profile. `appsscript.json` has exactly 4 scopes: `forms.currentonly`, `gmail.compose`, `script.external_request`, `script.scriptapp`. A test fails if a scope is added or a broad service (SpreadsheetApp, DriveApp, Session, GmailApp) is used.
- Lesson: for every scope ask "can an existing permission do this?" before adding a new one; extras like an archive Sheet cost Tim permissions he never asked for.

### 2026-11-19 — Identity file
- Tim: "we've worked for days but I don't know you yet."
- Action: `IDENTITY.md` (Dutch, for Tim): who the manager is, no memory between sessions (files are the memory), team overview, principles, this week's mistakes, what Claude knows about Tim, tips. Keep the team table and mistakes section current.

### 2026-11-19 — Manager persona "Max"
- Tim wants the manager to feel like a real person: name, tone, personality, hobbies.
- Action: persona Max at the top of `IDENTITY.md` (calm, direct, honest, coaching; sports images max once per conversation; motto "Eerst de feiten, dan de actie."). Clearly marked as a role played by Claude; CLAUDE.md always wins. CLAUDE.md §1 and §3 updated (Tim's own request, so done directly): read IDENTITY.md at session start and keep it current.

### 2026-11-19 — Bookkeeping folder must be a real folder in the project
- Situation: `Boekhouding` in the project became a Finder alias to a copy outside the project (`.../Tim Aarts/Claude/Boekhouding`), so the agent read and wrote outside the project without noticing.
- Lesson: an alias or symlink looks like a folder to Tim but sends work elsewhere; check with `file` before trusting a folder.
- Action: real copy in `Boekhouding/` (alias archived in `archive/`, git-ignored); `tools.bookkeeping` refuses to run when `Boekhouding` is not a real folder inside the project; `.claude/settings.json` denies Claude access to `/Applications/School/**`.


### 2026-11-19 — November bookkeeping approved
- Tim checked the November file, year overview and weekly report: "alles ziet er goed uit". First real Wednesday update on 25 Nov 2026; agent stays in training until then.

### 2026-11-19 — Invoice agent built
- Tim approved `finance-invoice-writer`: drafts from unbilled sessions, Tim approves, sends himself.
- Decisions: all numbers, numbering (ledgers + PDFs in `01 Verkoop Facturen/`), due date (payment term from config, 14 days) and booking in `tools/invoice.py`; PDF via reportlab in the layout of invoice 001. Fixed invoice details (KVK, BTW-id, IBAN, client address) taken from invoice 001 into `knowledge/private_bookkeeping.json` (not in git). Drafts never use up a number; `finalize` needs `--approved` and refuses overwrites, reused numbers and outdated drafts.
- Fixed from 001: "factuur bedrag" → "factuurbedrag", month names lowercase, term 25 → 14 days per config. Added lesson dates under the description so the client can check.
- Open: invoice 001 PDF says 16 Sep 2026, the ledger says 7 Oct 2026; Tim said not to ask about 001, so left as is. Sender address on 001 has no postcode/town.

### 2026-11-19 — Invoice layout approved
- Tim approved the layout of draft 002. Client on invoices: "Stichting Sint Jacob" (full legal name). Sender address gets postcode + town; postcode asked from Tim, never looked up online (would send his address to an outside service).

### 2026-11-20 — Friday run (automated)
- 5 candidates, all verified (pages opened), ~40 web calls; mode normal; top score 38 (UEFA Media Attendance Assistants). Weak week: no policy, project-lead or traineeship roles; three UEFA admin/logistics roles rank high on employer points alone.
- Proposals (need Tim's OK, not implemented):
  1. Update `knowledge/job_sources.md`: mark Krajicek, KNVB and VU pages as not working; add adidas `jobs.adidas-group.com/search/?locationsearch=Amsterdam`, Upfront via magnet.me and the Noord-Holland traineeship (recruits in February).
  2. Add policy/trainee boards (binnenlandsbestuur.nl/vacatures, werkenvoornederland filtered on VWS/sport) and ask Tim for LinkedIn alerts; broad WebSearch mostly returned dead (404/410) pages.
  3. Scoring: flag "no vacancy above X" weeks, or lower impact points for `operations_logistics`/`finance_admin` roles that Tim rates low.

### 2026-11-20 — Tim's ratings of the Friday run
- Ratings (role / org): UEFA Media Attendance 2, EURO Access 2, Event Workforce 2 (org not given as a number, but "UEFA is sowieso een goede organisatie"); Upfront Junior Recruiter 3 / 4 (Tim said 3.5 overall); adidas Partner BD Lead 1 / 5 (Tim said 2.5 overall). All `skipped`: no letters this week.
- Tim's preferences: no media or social media roles (confirms ASICS); dislikes recruiting; junior level is a plus; 5+ years of experience = never getting in; an Upfront children's event role would be a 10. Watch for traineeships above all.
- Open: ratings are whole numbers, so half points (3.5, 2.5) are kept only in `feedback`. Asked Tim for a UEFA org rating, otherwise three role-2 ratings teach that federations are weak (the ASICS problem).

### 2026-11-20 — Networking event scout (plan approved)
- Tim wants to network: every Friday an overview of fitting networking events, and go to one event per month that helps his future.
- Tim: no price limit, available any day and time, doesn't know yet what he likes: "send things, I rate them 1–5, you learn".
- Action: `career-event-scout` + `tools/events.py` (scoring, six-week window, excluded organisers from `job_filters.json`, log `logs/events.csv` tracked in git, learning from ratings, month check). Fixed weights are small and the learned bonus large (±25, 3 ratings per feature), so Tim's ratings drive the ranking. A rating after attending overrides the rating beforehand. Price is shown and learned as a band, never filtered. Added to the `career-friday-run` scheduled task.
- Trial run (2026-11-20): 7 candidates, 5 shown, scores 17–29; quiet holiday period, nothing in Amsterdam/Haarlem, nothing from dream employers. Best source: Vereniging Sport en Gemeenten agenda. Mulier and cruyffinstitute.org agendas don't work; KSB uses `/events/`.
- The tool ranked a fully booked event #1: added `sold_out` (excluded). Multi-date events: first date in the window. Missing year: only if the weekday matches.
- Open proposal: more sources (Sports Innovation League/Rockstart, NOC*NSF, Net Impact Amsterdam, Amsterdam Sportgala).

### 2026-11-20 — First event ratings, no online events, training round
- Tim's ratings: online talkshow Europe 4, DCSEM sports medicine congress 4 ("te hoog gegrepen betekent niet oninteressant"). No number yet for the Didam webinar; Werkconferentie and Workshop XL needed an explanation first.
- Lesson: Tim can't rate an event from its title; the overview must say what it is, who comes and what you do there. Agent output now has a "Wat is het" part.
- Tim: "online is gewoon niet wat ik zoek": `tools/events.py` now excludes online events.
- Training round: 20 varied fictional in-person events logged with status `training` (`https://training.invalid/eNN`); rating sheet `output/career/event_training_2026-11-20.md`; scores hidden to avoid anchoring.

### 2026-11-23 — Event training ratings 1–10
- Ratings: 1→4, 2→4, 3→3, 4→5, 5→2, 6→4, 7→4, 8→5, 9→3, 10→4 (Tim corrected 10 from 5 to 4 himself). Reasons are stored in `logs/events.csv`.
- Lesson: price is a timing question, not a dislike. Tim wants free events first and paid congresses later. The learned `price:` bonus will capture "now"; ask again after his first events.
- Tim asked whether the €395 congress is worth it: give an honest view, but the decision is his.

### 2026-11-23 — Event training ratings 11–20 and first check of the model
- Ratings: 11→5, 12→4, 13→3, 14→3, 15→4, 16→5, 17→5, 18→5, 19→4 (Tim corrected his 5 himself), 20→2. Average of all ratings ≈ 3.9: Tim rates generously.
- Check: leave-one-out Spearman between tool score and rating is only 0.2 (centring on Tim's mean instead of 3 gives 0.12, so not adopted). The features (topic, type, price, place) miss what really drives him: "does this fit my next step now".
- Decision: no scoring change yet. Real events with ratings before and after attending will tell more than fictional ones; re-check after ~10 real ratings.

### 2026-11-23 — First automatic Monday reminder went well
- Tim: the Apps Script reminder draft (Monday ~12:45) was correct and he sent it.
- Action: `bootcamp-reminder` marked active in the registry and IDENTITY.md. Phase 2 (auto-send) for reminder and promotion only after two error-free weeks, with a CLAUDE.md change approved by Tim.

### 2026-11-23 — Ratings for trial-run events
- Werkconferentie Sportinnovator 3 (good network, topic doesn't appeal), Workshop XL 2 (aimed at people already working at a municipality; 10–20 people is too small and too intense). Didam webinar not rated: it is online, so it is filtered out anyway.
- Lesson: "small group" is not automatically a plus for Tim; a training day for people already in the job scores low (same pattern as the fundraising masterclass).
- Approved by Tim: `small_group` now earns 0 network points (was +3).

### 2026-11-23 — Location moved to the balcony of team 2
- Tim: from now on the session is on the (covered) balcony of team 2, not the binnenplaats.
- Action: promotion mail says "op het balkon van team 2"; rain advice in the reminder (Python and Apps Script) now reads "We staan op het overdekte balkon van team 2, dus regen is geen probleem."; `knowledge/bootcamp.md` and `mail-promo-writer` updated. The Apps Script copy in Tim's Google account must be re-pasted by Tim to take effect.

### 2026-11-23 — Invest department: from tickets to crypto paper trading
- Tim wanted a ticket-resale predictor (TicketSwap). TicketSwap blocks bots, and its rules (pasted by Tim) forbid scraping and reselling with purely commercial intent; margin after fees and the 120% cap is ~€1–7 per ticket. Proposed paper trading; Tim chose crypto paper trading instead (automatic public data, fast feedback).
- Hard rule approved by Tim: invest never uses real money, accounts, wallets or keys; switching only via a separate decision after ≥3 months of good results (CLAUDE.md §6).
- Tim's goal: learn, steady results, horizon ~5 years. No pings per paper trade; Thursday analysis in the Claude app; alert only when the watch breaks or the pot moves >5 pp away from the market (both directions). Rule changes need his approval (overfitting risk explained).
- Tim wants sparring: keep giving honest feedback and better ideas (confirmed again).
- First backtest (2 years hourly BTC/ETH, 70/30 split): no rule beat buy-and-hold convincingly on unseen data; best-on-train (breakout_24_336) only marginally beat buy-and-hold on test (-11.9% vs -13.9%, within noise), and the active default sma_cross_24_168 did -19.1%, around coin-flip level -18.3%). Lesson: hourly rules are mostly noise plus fees; slower rules fit Tim's 5-year horizon better — candidate for the first Thursday proposal.
- launchd job runs fine from ~/Documents with the framework Python (no privacy block).

### 2026-11-23 — Crypto learning loop sharpened (approved by Tim)
- Tim asked whether the tactic works long-term. Honest answer: as a learning project yes; beating the market structurally unlikely; trend rules mainly reduce deep drops. Risk named: testing many rules on the same data finds luck, not skill.
- Built: slow daily rules (`d_*`), largest-drop measure (backtest + report), 4-year backtest, and a 28-day minimum before the active rule may be switched (live paper weeks are the real test).
- 4-year backtest (test = last ~14 months, a falling market: buy-and-hold -48%, largest drop -67%): best daily rules -4% to -6% with drops of -13% to -38%; active hourly rule -47%; coin flip -34%. In the rising train period buy-and-hold (+372%) beat every rule (best daily +178%). Confirms: trend rules protect in crashes and lag in rallies. One test period in one market type is not proof.
- Earliest possible switch from `sma_cross_24_168`: 2026-12-21.

### 2026-11-23 — Pushing works from Claude Code
- Push kept failing (no GitHub login for command-line git). Homebrew cannot build gh on this Intel Mac (outdated Command Line Tools); installed the official gh .pkg instead (checksum verified), Tim ran `gh auth login`, `gh auth setup-git` links git. Claude can now push itself.

### 2026-11-24 — LinkedIn leads feed the Friday run
- Tim pasted 9 LinkedIn vacancies (lnkd.in links) to include on Friday.
- Action: leads stored in `logs/job_leads.md` (local, status open/processed); `career-job-scout` must turn every open lead into a candidate by looking it up on the employer's own site or a public job board (never opening LinkedIn), else `verified: false` with Tim's link; the scheduled Friday task brief and checks updated accordingly; output marks them "(jouw LinkedIn-tip)".
- Noted: several leads hit known filters or low-fit role types (finance head, account executive = commercial sales, Australia); the run reports why each lead did not reach the top 5.

### 2026-11-24 — Team Visma lead rated 5, scoring missed it
- Tim rated the Team Visma | Lease a Bike travel & planning coordinator (LinkedIn lead) a 5 and asked for a letter; real page found on teamvismaleaseabike.nl, deadline 29 November.
- The scoring tool gives it only 28 (no domain points for operations at a top professional sports team; operations_logistics not preferred). Proposal for Tim: a domain or bonus for roles inside elite/international sports organisations (UEFA, top cycling/football teams).
- Letter rule clarified in `letter_style.md`: Tim wants the short skill sentence in every letter (QA flagged it twice against the old wording).

### 2026-11-24 — New facts from Tim's letter feedback
- Tim added facts for the Team Visma letter; recorded in `knowledge/profile.md` (Tim's own statements, 2026-11-24): English excellent, can get by in Spanish (formally ~A1–A2 per 18-11 interview — flagged to Tim), earlier gap year of travel with lots of self-planning and hotel booking, Argentina for the internship, cycling affinity (Tour de France family tradition), Mathematics B = problem-solving.
- Lesson: the writer listed "affinity with cycling" and "booking hotels" as gaps; Tim had both. The writer's notes should ask Tim about such gaps (as it did) — and I should pass those questions on before finalising.

### 2026-11-24 — AI skill added; CV-advice agent requested
- New fact in `profile.md` (Tim): works well with AI; built a small program with AI at Sint Jacob, which contributed to the grade 10.
- Tim asked for an agent that gives tailored CV advice per vacancy; plan proposed first (new agent → plan + approval, CLAUDE.md §2).

### 2026-11-24 — CV advisor built (plan approved by Tim)
- New agent `career-cv-advisor`: per selected vacancy, advice with exact OUD → NIEUW text changes; manager applies approved changes to a COPY of Tim's Canva CV (`DAG0GcTT33A`, never the original) and exports a PDF. Canva connected by Tim. CV text snapshot in `knowledge/private_cv_en.md` (not in git).
- Trial (Team Visma): 8 CV lines conflict with `profile.md` (e.g. "Student" title, language levels, T.A Vitality bootcamp is for employees not residents, "managing budgets", Canva "Proficient"). The CV overstated things before; the advisor must keep checking every line.
- Gaps: Tim's Dutch CV exists only as a PDF (no Canva design found); copying files from outside the project folder was refused, so Tim drags them in himself.

### 2026-11-24 — First tailored CV exported from Canva
- Applied the approved advice to a copy (`DAHb0Sbr2mg`, "Tim Aarts CV - Team Visma Lease a Bike"); original `DAG0GcTT33A` untouched. Exported to `output/career/cv_tim-aarts_team-visma-lease-a-bike_2026-11-24.pdf`.
- Lesson: Canva text boxes do not reflow — a longer Sint Jacob text pushed "Grade: 10" onto the next heading. Fix: keep replacement texts about as long as the originals; check the thumbnail after every edit; show Tim the preview before committing. Rule added to `career-cv-advisor`.
- Trade-offs made for space: "budget/medical" dropped at Sint Jacob, Canva skill swapped for AI tools, title "Graduate".

### 2026-11-24 — Letter writer trained on four approved letters
- Tim: letters must above all be tailored to the organisation he applies to.
- Action: `knowledge/letter_style.md` now has a tailoring section (research their own site; ≥4 organisation-specific elements; swap test), a structure blueprint from the Mulier, UEFA, Happy2Move and Visma letters, tone rules and "check profile before calling something a gap". `career-cover-letter-writer` got an organisation-research step, a tailoring self-check and fixed note sections (incl. "Vragen voor Tim"); `qa-fact-checker` checks tailoring.

### 2026-11-24 — CV profile stays general
- Tim found the tailored Profile section too job-specific. Profile now general (personality: energetic, entrepreneurial, eager to learn, thrives on challenges); tailoring happens in experience lines and skills. Rule + approved text added to `career-cv-advisor`; Visma CV copy updated and re-exported.

### 2026-11-24 — First B2B prospect list for T.A Vitality (Haarlem)
- Tim wants large Haarlem employers to offer one movement session per week (cold calls/mails/visits). Manager did the research directly (no agent yet); list in `output/sales/prospects_haarlem_2026-11-24.md` (12 organisations + Industriekring Haarlem as network entry).
- Lesson: no public ranking of Haarlem's largest employers exists; headcounts come from scattered annual reports and are often years old, so every figure carries source + year. No contact names collected (privacy); Tim looks up HR/vitality contacts himself.
- Open for Tim: price/format of a session, available times, region (Haarlem only or also Heemstede/Hoofddorp/Velsen). If this becomes recurring, propose a `sales-lead-scout` agent.
- Tim's criterion (same day): many employees at ONE location. Care chains spread over nursing homes (Zorgbalans) don't qualify — only physios/higher-educated staff would join; Teva (one factory site) is "perfect", Spaarne Gasthuis Haarlem-Zuid a good option. List v2 ranks by expected headcount per site; spread-out organisations moved to "afgevallen".

### 2026-11-24 — Website for T.A Vitality: Tim's brief
- Goal: employers (e.g. Teva) see that T.A Vitality exists and can fill in a contact form or book an introductory call; Tim can refer prospects to it.
- Content: weekly movement sessions only. No prices. Small, focused, clear, easy to scan.
- Public details: Tim's name, phone number and KvK number. NO e-mail address. Do NOT name Sint Jacob as a client. No photos, no logo yet.
- Colours: Tim is defining them via a separate branding chat and will come back with them.
- Domain: none yet. First build the site and see if it works; domain (costs money) is a later decision.
- Privacy: phone and KvK stay out of git (placeholders in the source, filled from `knowledge/private_*` at build time).
- Built (same day): `site/index.template.html` + `site/config.json` (colours, `form_url`, `booking_url`) → `.venv/bin/python -m tools.site_build` → `output/site/index.html`. Without links the buttons fall back to "Bel voor een kennismaking". Tests guard: no "Jacob", no "@", no "€" on the page. Placeholder colours until Tim's branding chat delivers.

### 2026-11-24 — Brandbook T.A Vitality: Tim's interview answers + concept v1
- Story: work and life are merging; employers should care for their people; movement is the best way to break up or end a workday; people should go to work with a good feeling ("way of living", not just a paycheck).
- Feel: timeless, "a good product" (quality, not luxury), honest. Avoid: exuberant, gold, high-end, gym, in-your-face, testosterone, muscles. Wanted: smooth, beautiful, product-design-like.
- Colour: a red slightly darker/different than normal red; a bit daring, something that grabs. References: Apple, Netflix, Spotify, On.
- Logo: undecided; does not have to be a V/TA monogram; asked for 4 sketches. No slogan idea.
- Clothing: clean, ONE colour, small logo on the back. Website tone: "u", businesslike, direct, honest.
- Earlier attempt "Break V." (Tim's artifact): terracotta #AE5D4E, peach, Fraunces serif; Tim was not satisfied. Concept v1 deliberately goes deeper red, sans-serif (Inter Tight/Inter), fewer warm tones.
- Concept v1: `output/brand/brandbook_2026-11-24.html` (Vitality-rood #A3302B, Inkt, Kalk, Steen, Blos; logos A–D; 5 slogans; clothing rules). Contrast/CMYK computed in Python. After Tim's approval: `knowledge/brand.md` + colours into `site/config.json`.
- Lesson: files outside the project folder (Tim's school branding files) cannot be read — ask Tim to drag them into the project folder.
- Decisions (same day): logo B (two circles); name "T.A Vitality" with ONE dot (deliberate signature), lowercase "t.a vitality" in logo; the dot is a brand device; red #A3302B approved; slogan "werk in beweging.".
- Tim's wish: stay authentic — not like other vitality brands and not like typical Claude/AI design. Lesson: v1 was exactly the Claude default (cream background, Inter, rounded cards, pill tags, numbered kickers). v2 deliberately: white + ink + one red, straight corners, hairlines, Archivo at 112% width, lowercase headings with red dot, lens as graphic device. Anti-pattern list lives in `knowledge/brand.md` — every agent that makes visual or written output follows it.
- Brand is now in `knowledge/brand.md` + `knowledge/brand/logo/*.svg`; website colours updated in `site/config.json`. Website layout itself (rounded cards, system font) is not yet restyled to the brand.
- Feedback v2: "te wit" — Tim liked the full red cover. Brandbook now alternates red/ink/beton/white sections with large cropped circles; ratio white 40 / red 30 / ink 25. Lesson: "anders" must not become "leeg"; character comes from bold full surfaces, not decoration.
- Feedback v3: "te grote vlakken, je moet inzoomen". Lesson: check documents at normal size on laptop AND phone width, not zoomed out; cap block heights (logo tiles ~170 px), keep text ≥14 px and headings moderate. A brandbook is read, not a poster.
- Feedback v4: compact version "te compact" → reverted to the large version (red/ink surfaces, big blocks). Compact copy archived as `output/brand/brandbook_v2-compact_2026-11-24.html`. Lesson: make one small step per feedback round instead of a full resize; when Tim says "inzoomen" ask which part feels too big.
