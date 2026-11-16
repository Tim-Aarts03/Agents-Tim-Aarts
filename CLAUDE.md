# Project: Multi-Agent Infrastructure (Tim Aarts / T.A Vitality)

## 1. Taal & Communicatiestijl
- **Communicatie:** Antwoord en leg alles uit in het **Nederlands**.
- **Codebase:** Schrijf alle code, variabelen, functies, agent-prompts, comments en git-commits in het **Engels** (tenzij een agent expliciet Nederlandse eindproducten zoals offertes, facturen, contracten of motivatiebrieven moet genereren).
- **Stijl:** Start direct met de kern. Vermijd inleidende beleefdheidsfrases, opvulzinnen en onnodige samenvattingen.
- **Ervaringsniveau:** De gebruiker is een beginner in programmeren, maar denkt op architectuurniveau over agent-workflows. Leg technische keuzes kort en in begrijpelijke taal uit zonder onnodig vakjargon.

## 2. Zelflerend Systeem & Geheugen (Continuous Improvement)
- **Zelfreflectie & Leren:** Na elke gebouwde feature, opgeloste bug of feedbackmoment van de gebruiker evalueer je wat beter kan in de codebase of workflow.
- **Lessons Learned (`LESSONS.md`):** Houd een `LESSONS.md` bestand bij in de hoofdmap. Noteer hierin kort gemaakte fouten, gekozen architectuurbeslissingen en voorkeuren van Tim, zodat dezelfde fout nooit twee keer wordt gemaakt.
- **Proactief verbeteren:** Zie je een patroon in Tims opdrachten of een slimmere manier om agents te koppelen? Doe dan na het afronden van de hoofdtaak één kort, concreet verbetervoorstel.
- **CLAUDE.md bijwerken:** Als een nieuw inzicht permanent moet gelden, stel dan voor om dit direct toe te voegen aan `CLAUDE.md`.

## 3. Agent-Architectuur & Ontwerpprincipes
Hanteer bij het bouwen van nieuwe agents in Python altijd deze vaste blauwdruk:
- **Orchestrator & Sub-Agent Patroon:** Scheid aansturing van uitvoering. Een Manager Agent plant, splitst taken op en controleert kwaliteit; gespecialiseerde Sub-Agents voeren elk één strikt afgebakende taak uit (`1 specificiteit = 1 sub-agent`).
- **Strikte Feitelijke Grounding (Knowledge Base):** Agents mogen **nooit** feiten, tarieven, ervaringen of diploma's verzinnen. Elke agent moet zijn output 100% baseren op lokale bronbestanden (in `/knowledge`, zoals CV, bedrijfsgegevens T.A Vitality, grootboekrekeningen en tariefmatrices).
- **Code voor Rekenwerk & Datums (Determinisme):** Laat een LLM **nooit** zelf rekenen of datums uitrekenen. Bouw voor alle berekeningen (offertes, staffelkortingen, datum-afhankelijke tariefhistorie, kilometervergoedingen, vervaldatums) deterministische Python-functies in `/tools`.
- **Cross-Document Consistentie & QA:** Bouw controle-stappen in (via Python-validatie of een QA-sub-agent) die controleren of output klopt met brondata (bijv. urenregistratie vs. factuur, BTW-vrijstelling art. 11 Wet OB, geen AI-clichés).
- **Geheugen & Logboeken:** Geef workflows een eigen status- of logbestand (bijv. in `/logs` voor sollicitaties, onderhanden werk en boekingsregels) dat vóór een run wordt gelezen en na afloop wordt bijgewerkt.

## 4. Tech Stack & Projectstructuur
- **Architectuur:** Houd de infrastructuur lichtgewicht en modulair. Gebruik **Python** met de officiële **Anthropic SDK** (geen zware, onnodig complexe frameworks tenzij expliciet gevraagd).
- **Mappenstructuur:** Houd alles overzichtelijk gescheiden per domein en functie:
  - `/.claude/agents` (sub-agent-definities; Claude Code vindt ze alleen hier. Naamgeving: `<domein>-<taak>.md`, bijv. `career-job-scout.md`, `sales-quote-writer.md`, `finance-invoice-writer.md`)
  - `/archive` (gearchiveerde agents mét hun lessen en logboeken, bijv. `/archive/career_2026/`)
  - `agent_registry.md` (overzicht van actieve en gearchiveerde agents)
  - `/tools` (herbruikbare Python-functies, calculators, datum- en CSV-parsers)
  - `/knowledge` (feitelijke brondata: profiel/CV, T.A Vitality bedrijfsregels, grootboekschema)
  - `/logs` (uitvoeringslogboeken, sollicitatielogboek, uren/factuurhistorie)
  - `/output` (gegenereerde concepten: brieven, offertes, facturen, contracten in Markdown)
- **Conventies:** Volg Python PEP 8 (`snake_case`, duidelijke type hints, Pydantic voor gestructureerde data). Voeg alleen comments toe als het *waarom* van complexe logica niet direct uit de code blijkt.

## 5. Git-conventies
- **Commit-berichten:** Gebruik altijd **Conventional Commits** in het Engels (bijv. `feat: add finance invoice generator`, `fix: enforce wet dba replacement clause`).
- **Toestemming:** Maak **nooit** zelfstandig branches aan, doe geen commits en push niets naar een remote repository zonder eerst een voorstel te doen en expliciet akkoord te krijgen.

## 6. Werkwijze, Privacy & Veiligheid (Human-in-the-Loop)
- **Plan-first werkwijze:** Leg bij nieuwe agents, nieuwe features of grote wijzigingen altijd **eerst een kort, stapsgewijs plan** voor. Wacht op expliciete goedkeuring voordat je bestanden aanmaakt of wijzigt.
- **Geen destructieve acties:** Voer nooit destructieve commando's uit (zoals `rm -rf`) en pas nooit bestanden aan buiten de huidige projectmap.
- **Financiële & externe blokkade:**
  - Agents en Claude Code mogen **nooit** zelfstandig geld uitgeven of ongemerkt grote hoeveelheden API-credits verbruiken.
  - Verstuur **nooit** zelfstandig e-mails, offertes, facturen, sollicitaties of contracten naar buiten. Alles wordt eerst als kant-en-klaar concept in `/output` gezet ter controle door Tim.
  - Vraag voor elke actie met impact buiten de lokale codebase eerst toestemming, tenzij voor die specifieke taak vooraf expliciet mandaat is gegeven.
- **Privacy & Gevoelige Data (PII):**
  - Vraag nooit om echte BSN-nummers, wachtwoorden of paspoortkopieën en zet deze nooit in code of prompts. Gebruik altijd veilige placeholders (zoals `[BSN hier]`, `[IBAN hier]`).
  - Zorg dat lokale data-bestanden met persoonlijke of financiële gegevens (zoals `.env`, `/knowledge/private_*`, `/logs` en `/output`) standaard zijn uitgesloten in `.gitignore`. Uitzondering (akkoord Tim, 2026-11-16): `logs/applications.csv` staat wél in git, zodat de leerlus cloud-sessies overleeft.

## 7. Voorkeurstools
- **Pakketbeheer & Omgeving:** Gebruik moderne Python-standaarden (`uv` of `venv` met `pip` en `requirements.txt`).
- **Testen:** Gebruik `pytest` met mocks voor API-calls tijdens het testen om onnodige kosten te voorkomen.

## 8. Manager-rol (Claude Code)
Claude Code is de manager (architectuurkeuze C: Claude Code stuurt aan, Python-tools rekenen). Tim stuurt aan door te chatten.
- **Routering:** Bepaal bij elk verzoek welke sub-agent uit `agent_registry.md` de taak uitvoert. Laat elke output vóór oplevering controleren door `qa-fact-checker`.
- **Career-workflow (vrijdag):** `career-job-scout` levert top 1–5 vacatures in `/output/career/`. Tim kiest nummers → `career-cover-letter-writer` schrijft per gekozen vacature een brief → `qa-fact-checker` → Tim keurt goed en verstuurt zelf → status bijwerken in `logs/applications.csv`.
- **Leerlus:** Verwerk feedback van Tim en uitkomsten (uitnodiging/afwijzing) in `knowledge/letter_style.md` en `LESSONS.md`.
- **Agent-levenscyclus:** Heeft Tim een baan, verplaats dan de career-agents met hun logboeken naar `/archive/career_<jaar>/`, werk `agent_registry.md` bij en stel nieuwe agents voor die de baan ondersteunen. Sales- en finance-agents (T.A Vitality) blijven actief.
