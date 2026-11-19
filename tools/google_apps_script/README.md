# Bootcamp-formulier: maandagreminder en dinsdag leegmaken

Twee scripts die in je eigen Google-formulier draaien. De e-mailadressen van deelnemers blijven in je Google-account; Claude krijgt ze niet.

| Script | Wanneer | Wat |
|---|---|---|
| `bootcamp_reminder.gs` | maandag ± 12:45 | maakt de vaste reminder (met weeradvies) voor iedereen die zich heeft aangemeld, deelnemers in **BCC**. Fase 1: **concept in Gmail** + een mailtje aan jezelf "Reminder staat klaar". Jij klikt op Verzenden. |
| `clear_bootcamp_responses.gs` | dinsdag ± 20:00 | kopieert alle aanmeldingen naar de Sheet **"Bootcamp aanmeldingen archief"** en wist daarna de antwoorden, zodat dezelfde link de week erna weer werkt. |

Beide doen niets op een andere dag, ook niet als je ze per ongeluk start. De reminder wordt maximaal één keer per maandag gemaakt en niet als niemand zich heeft aangemeld.

## Eenmalig installeren (± 10 minuten)
1. Open je vaste aanmeldformulier in Google Forms (bewerkmodus, niet de invul-link).
2. Klik rechtsboven op de **drie puntjes ⋮ → Apps Script**. Er opent een nieuw tabblad.
3. Verwijder de voorbeeldcode in `Code.gs` en plak de **volledige** inhoud van `clear_bootcamp_responses.gs`.
4. Klik links naast "Bestanden" op **+ → Script** en noem het `bootcamp_reminder`. Plak daarin de **volledige** inhoud van `bootcamp_reminder.gs`.
5. Klik op **Opslaan** (💾). Geef het project een naam, bijv. "Bootcamp".
6. Kies bovenin in de keuzelijst **`reminderDryRun`** en klik **Uitvoeren**.
   - Google vraagt toestemming (formulier, Gmail, Sheets, internet voor het weer): kies je account → **Geavanceerd** → **Ga naar Bootcamp (onveilig)** → **Toestaan**. Dit is normaal voor een script dat je zelf hebt toegevoegd.
   - Onderin zie je het aantal deelnemers en de mail die gemaakt zou worden. Er wordt niets verstuurd.
7. Kies **`dryRun`** en klik **Uitvoeren**: je ziet hoeveel aanmeldingen gewist zouden worden. Er wordt niets gewist.
8. Kies **`installReminderTrigger`** → **Uitvoeren**. Kies daarna **`installTrigger`** → **Uitvoeren**.
9. Controle: klik links op het **wekker-icoon (Triggers)**. Je ziet twee triggers: `createReminder` (maandag) en `clearResponses` (dinsdag).

## Goed om te weten
- Het e-mailadres wordt gelezen uit de vraag met "mail" in de titel (of uit "e-mailadressen verzamelen" als dat aanstaat).
- Wissen kan niet ongedaan worden gemaakt; het archief is je back-up. De Sheet verschijnt na de eerste dinsdag met aanmeldingen.
- Is het weer niet op te halen, dan gaat de reminder zonder weeradvies en staat dat in het mailtje aan jezelf.
- Stoppen: verwijder de trigger via het wekker-icoon. Gaat de bootcamp een week niet door, zet dan beide triggers die week uit.
- **Fase 2 (automatisch verzenden)** pas na twee foutloze weken én jouw akkoord: dan wordt `REMINDER_SEND_AUTOMATICALLY` op `true` gezet en plak je de nieuwe versie.
- Verandert de remindertekst of de weerregel, dan moeten de Python-tools en dit script samen worden aangepast; de test `tests/test_apps_script_reminder.py` bewaakt dat.
