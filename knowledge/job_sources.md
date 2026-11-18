# Job sources

Search only public pages. Never log in or scrape LinkedIn. Never propose organisations in `knowledge/job_filters.json` (FIFA, Red Bull, Atleetfabriek).

**How to use:** open the URLs below directly (one fetch each) before doing any general WebSearch. Broad searches mostly return expired vacancies. If a URL stops working, move it to "Not working" with the date and record it in `LESSONS.md`.

## Employers: career pages (checked 2026-11-18)
| Organisation | URL | Note |
|---|---|---|
| Jeugdfonds Sport & Cultuur | https://jeugdfondssportencultuur.nl/vacatures/ | vacancies are posted as news items |
| Krajicek Foundation | https://www.krajicek.nl/over-ons/team-en-bestuur/vacatures/ | mostly volunteer/graduation places |
| Kenniscentrum Sport & Bewegen | https://www.kenniscentrumsportenbewegen.nl/over-ons/werken-bij/ | |
| Mulier Instituut | https://www.mulierinstituut.nl/werken-bij/ | |
| Gehandicaptensport Nederland | https://www.gehandicaptensport.nl/organisatie/vacatures | |
| NOC*NSF | https://www.nocnsf.nl/vacatures | |
| KNVB | https://www.werkenbijdeknvb.nl/ | |
| Happy2Move | https://happy2move.nl/vacatures/ | |
| Sportbedrijf Zaanstad | https://www.sportbedrijfzaanstad.nl/vacatures/ | mostly swimming instruction |
| Gemeente Zaanstad | https://werkenbij.zaanstad.nl/ | policy / project roles only, NOT buurtsportcoach |
| VU Amsterdam | https://werkenbij.vu.nl/ | movement science research support |
| **UEFA** (dream: UEFA Foundation) | https://www.uefa.com/insideuefa/careers/job-opportunities/ | works via WebFetch (not via curl); vacancies open on emp.jobylon.com |
| **Adidas** (dream) | https://careers.adidas-group.com/ | |
| Nike | https://careers.nike.com/ | |

## Employers without a working vacancy page yet
- **Upfront** (dream employer): `/vacatures` gives 404. Tim: share the right link if you know it.
- **Johan Cruyff Foundation**: no vacancy page; vacancies appear on LinkedIn only. Tim pastes them.
- **Gemeente Amsterdam / Haarlem**: guessed werkenbij-domains do not resolve. Use WebSearch `site:` queries until a working URL is known.
- **Ajax / AZ foundations**: no vacancy page found.
- ASICS EMEA (Hoofddorp): found via magnet.me only.

## Traineeship providers
Traineeships are hard to find by searching. Check these pages every run; when a page states a recruitment period, write it in the "Recruits" column (never guess it).

| Provider | URL | Recruits |
|---|---|---|
| Rijksoverheid / overheid (werkenvoornederland) | https://www.werkenvoornederland.nl/starters/traineeships | unknown |
| Provincie Noord-Holland | https://www.noord-holland.nl/Over_de_provincie/Werken_voor_Noord_Holland | unknown |
| NOC*NSF | https://www.nocnsf.nl/vacatures | unknown |

## Job sites
- indeed.nl: search results pages only (individual job pages return 401; never use a link you did not see).
- nationalevacaturebank.nl, sector-specific boards.

## Not working (2026-11-18)
- werkzoeken.nl (403), jobbird (redirects to other vacancies), magnet.me vacancies older than a few weeks (410), consultancy.nl/traineeships (nothing usable).

## LinkedIn
- Tim sets up LinkedIn job alerts (e.g. "traineeship sport", "beleid sport", "fondsenwerving") and pastes or forwards relevant vacancies into the chat.

_Add or remove sources based on which ones deliver good vacancies (record in LESSONS.md)._
