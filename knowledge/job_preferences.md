# Job preferences — Tim Aarts

Used by `career-job-scout`. Scores are computed by `tools/job_scoring.py`, never by the LLM.

## Goal (Tim, 2026-11-17)
A job (not an internship; a traineeship is welcome) that:
1. **looks strong on the CV** (well-known or respected organisation, real responsibility);
2. **builds a strong network** (works with influential, experienced people);
3. **puts Tim in many learning situations** (variety, responsibility, exposure to leadership).
Learning value outweighs salary.

## Domains (in order of fit)
1. Sport/movement for vulnerable groups (children in disadvantaged neighbourhoods, low-income children, minorities) — `sport_for_vulnerable_groups`
2. Sport + technology — `sport_tech`
3. Roles supporting movement sciences (research, health, exercise) — `movement_science`
4. Large commercial sports brands with strong learning environment (e.g. Nike, Adidas) — `sports_brand`

## Location
- Preferred: Amsterdam, Haarlem and places within ~10 km — list in `knowledge/preferred_places.json`.
- Hybrid/remote with Netherlands base: acceptable.

## Hours
- Preferred: part-time (combinable with pre-master Movement Sciences and T.A Vitality).
- Full-time: acceptable if the role is excellent.

## Hard filters
- Deadline passed → exclude.
- Internship (stage) → exclude. Traineeships are welcome.
- Requirements Tim does not meet (master's degree, years of experience) → lower score, not excluded.

## Learning from ratings
- Tim rates every proposed vacancy 1–5 (optionally with a reason).
- `tools/preference_learning.py` learns which domains, role types, organisation types and employment types Tim rates high or low, and adjusts scores by at most ±10 points.
- Known signals (Tim, 2026-11-17): an attractive company does not compensate for an unsuitable role (Upfront account manager, defence & security: rated 2).

## Sources
- (a) Public job sites and employer career pages — see `knowledge/job_sources.md`.
- (b) LinkedIn job alerts forwarded by Tim (LinkedIn may not be scraped automatically).
