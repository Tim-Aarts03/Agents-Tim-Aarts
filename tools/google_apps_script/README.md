# Bootcamp-formulier elke dinsdag leegmaken

Het script `clear_bootcamp_responses.gs` draait in je eigen Google-formulier. Elke dinsdag rond 20:00:
1. kopieert het alle aanmeldingen naar de Google Sheet **"Bootcamp aanmeldingen archief"** in je Drive;
2. wist het alle antwoorden in het formulier, zodat dezelfde link de week erna weer werkt.

Op andere dagen doet het niets, ook niet als je het per ongeluk start.

## Eenmalig installeren (± 5 minuten)
1. Open je vaste aanmeldformulier in Google Forms (bewerkmodus, niet de invul-link).
2. Klik rechtsboven op de **drie puntjes ⋮ → Apps Script**. Er opent een nieuw tabblad.
3. Verwijder de voorbeeldcode in `Code.gs` en plak de **volledige** inhoud van `clear_bootcamp_responses.gs`.
4. Klik op **Opslaan** (💾). Geef het project een naam, bijv. "Bootcamp leegmaken".
5. Kies bovenin in de keuzelijst de functie **`dryRun`** en klik **Uitvoeren**.
   - Google vraagt toestemming: kies je account → **Geavanceerd** → **Ga naar Bootcamp leegmaken (onveilig)** → **Toestaan**. Dit is normaal voor een script dat je zelf hebt toegevoegd.
   - Onderin zie je hoeveel aanmeldingen er nu zijn. Er wordt niets gewist.
6. Kies de functie **`installTrigger`** en klik **Uitvoeren**. Onderin staat: *Trigger installed: every Tuesday around 20:00*.
7. Controle: klik links op het **wekker-icoon (Triggers)**. Je ziet één trigger `clearResponses`, wekelijks op dinsdag.

## Goed om te weten
- Wissen kan niet ongedaan worden gemaakt; het archief is je back-up.
- De Sheet "Bootcamp aanmeldingen archief" verschijnt pas na de eerste dinsdag met aanmeldingen.
- Wil je stoppen: verwijder de trigger via het wekker-icoon.
- Gaat de bootcamp een week niet door: de antwoorden worden toch gewist. Wil je dat niet, zet de trigger dan die week uit.
