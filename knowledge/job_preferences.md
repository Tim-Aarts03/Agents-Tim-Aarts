# Job preferences — Tim Aarts

Used by `career-job-scout`. Scores are computed by `tools/job_scoring.py`, never by the LLM.

## Goal (Tim, 2026-11-17)
A job (not an internship; a traineeship is welcome) that:
1. **looks strong on the CV** (well-known or respected organisation, real responsibility);
2. **builds a strong network** (works with influential, experienced people);
3. **puts Tim in many learning situations** (variety, responsibility, exposure to leadership).
Learning value outweighs salary.

## Role (Tim, 2026-11-18)
- **Wants:** to lead and steer, set up projects, create and implement policy and make it work (`program_coordination`, `policy_advice`: bonus points).
- **Does not want:** buurtsportcoach or giving sports lessons in front of a group (`coaching_delivery`: excluded) — too superficial, not challenging enough.
- **From an employer:** freedom, a learning environment, challenge and honest feedback.

## What drives Tim's ratings (from 20 training ratings, 2026-11-18)
- **Highest:** big impact and scale (national/international), a strong network, learning from experienced people, traineeships with rotation, partnerships/fundraising for a good cause, policy work.
- **Lowest:** club management, event logistics, selling a product (sports nutrition), apps and start-ups that are not Tim's own (-10 points each), research that requires a master's.
- Hours and distance only matter for average roles; for dream roles 40 h and moving abroad are fine.

## Organisations
- **Dream employers:** Upfront, Adidas, UEFA Foundation.
- Must do good for the world. **Excluded:** FIFA, Red Bull (list in `knowledge/job_filters.json`).

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
- Buurtsportcoach / giving sports lessons (`coaching_delivery`) → exclude.
- Organisations in `knowledge/job_filters.json` → exclude.
- Requirements Tim does not meet (master's degree, years of experience) → lower score, not excluded.

## Learning from ratings
- Tim rates every proposed vacancy 1–5 (optionally with a reason).
- `tools/preference_learning.py` learns which domains, role types, organisation types and employment types Tim rates high or low, and adjusts scores by at most ±10 points.
- Known signals (Tim, 2026-11-17): an attractive company does not compensate for an unsuitable role (Upfront account manager, defence & security: rated 2).
- Known signals (Tim, 2026-11-18):
  - Graduate/traineeship programmes at large sports brands (ASICS EMEA) are the most interesting: much to learn and strong on the CV. Company + programme format = 5.
  - But the role must fit: merchandise = 3, social media / brand media = 1 (does not want it).
  - Delivering sport lessons (e.g. sports coach at mbo level) = 3: acceptable for a gap year, no long-term future. A nice organisation (Happy2Move) with a different role could be interesting.
  - Sport and movement support for adults in care (NAH, Ons Tweede Thuis): not for Tim.

## Sources
- (a) Public job sites and employer career pages — see `knowledge/job_sources.md`.
- (b) LinkedIn job alerts forwarded by Tim (LinkedIn may not be scraped automatically).
