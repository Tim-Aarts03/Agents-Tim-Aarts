# Bootcamp / beweegsessie — T.A Vitality

Source of truth for the bootcamp mails (Tim, 2026-11-18). Recipient addresses live in `knowledge/private_mail_recipients.json` (not in git).

## Fixed facts
- **What:** weekly beweegsessie (bootcamp) for employees of Sint Jacob. Free for participants (the organisation pays).
- **When:** every Tuesday, 16:15–17:00.
- **Where:** the covered balcony of team 2, Hof van Jacob, Haarlem (from 23 November 2026, Tim; before that the binnenplaats).
- **Max participants:** 12.
- **Running since:** June 2026.
- **Sign-up:** one fixed Google Form (name and e-mail), reused every week. Responses must be cleared after each Tuesday session so the same link works again.

## Recipient groups
- `hof_van_jacob`: employees of Hof van Jacob. Sent to one contact person, who forwards it to the rest (Tim has no access to the internal Sint Jacob mailing lists). Address in the private recipients file.
- `jacob_kliniek`: a few individual addresses at Jacob Kliniek (Tim cannot enter there himself).

## Schedule
| Mail | When | To |
|---|---|---|
| Promotion mail | Wednesday 07:00 | both groups |
| Reminder | Monday ~13:00 | everyone who signed up for Tuesday |

## Promotion mail
Structure (filled by `tools/bootcamp_mail.py`): greeting per group → **pitch of 1–3 sentences** (the only part that changes; written by `mail-promo-writer`) → date line → sign-up link → closing.
Signature: "Met vriendelijke groet,\nTim Aarts".

## Reminder (always the same text, plus weather advice)
```
!Reminder!

Wat leuk dat jij je hebt aangemeld voor de beweegsessie van morgen.
Vergeet je sportspullen niet mee te nemen.

Tot morgen!

Met vriendelijke groet,

Tim Aarts
```
Weather rules (`tools/bootcamp_weather.py`): below 12 °C → advise warmer clothing. Rain expected → mention the covered balcony of team 2.

## Earlier pitches by Tim (style examples; names of participants replaced by [naam])
1. "Koppel jezelf los na een lange werkdag en doe gratis en voor niks mee met de wekelijkse beweegsessie op Hof van Jacob."
2. "Er wordt gelachen, bewogen en gezond gesnackt. De wekelijkse beweegsessie op dinsdagmiddag is sinds juni al een groot succes onder de medewerkers van Sint Jacob. Meld je aan via de onderstaande link en sluit je werkdag op een plezierige manier af."
3. "Afgelopen week zijn de eerste Sint Jacob sport T-shirts uitgereikt aan de meest trouwe deelnemers van Sint Jacob. Meld je snel aan en krijg jouw T-shirt na de 5e deelname."
4. "Laat jezelf van je beste kant zien en kom in beweging tijdens de wekelijkse beweegsessie op Hof van Jacob."
5. "Vandaag wisten [naam] en [naam] al ver boven hun niveau uit te stijgen!" (to team Jacob Kliniek)
6. "Hof van Jacob wordt elke week een stukje vitaler door de wekelijkse beweegsessie. Dinsdag 13 oktober staat er om 16:15 een nieuwe sessie op de planning en het belooft een groot succes te worden."
7. "Sinds het begin van de beweegsessies waren er niet meer dan 8 deelnemers per sessie. Dit record wisten jullie met 10 deelnemers vanmiddag met kinderlijk gemak te verbreken! Dat is het vermelden waard; nogmaals dank voor jullie enthousiasme 👏👏👏."
8. "Black Friday-deal van de week: een middag vol energie, een leeg hoofd en een hoop plezier. Meld je aan en sluit je werkdag in beweging af op Hof van Jacob! 💪" (Tim's own edit of the 25 Nov draft: the reference for length and tone)

## Style
- Warm, energetic, positive. "je/jullie".
- Facts in a pitch (participant numbers, records, T-shirts, names) ONLY if Tim gave them this week or they are in this file. Never invent them.

### Learned from Tim's ratings (training round 2026-11-18, 20 pitches)
- **Length:** 2–3 sentences. A single sentence feels too short and bare (rated 3), even when it is powerful.
- **Always:** emotion + a clear call to action ("meld je aan", "neem een collega mee", "doe mee"). Energy over calm.
- **Emoji:** 1–3 fitting emoji earn extra points (🌿 💪 🤝😊 ⚡🔥). No "cool" emoji like 😎.
- **Hooks rated 5:** clearing your head / leaving the busy day behind; T-shirt after the 5th session (triggers people who came once); bring a colleague / do it as a duo; energy boost for the rest of the week; turning dark November afternoons into something fun (question + exclamation + emoji).
- **Topical hooks are welcome:** a current event (e.g. Black Friday for a "deal" line) lifts a pitch from 4 to 5.
- **Avoid:** the attendance record of 10 (not impressive), limited places / "max 12", who pays ("de organisatie betaalt"), rain and weather (standard; the balcony is not a selling point), sweat or anything that sounds unpleasant, framing that sounds gloomy ("donkerder") without turning it into energy.
- **Tim's edit of 25 Nov (follow this):** 2 sentences: one hook sentence + one call to action. One emoji at the end. He cut "het kost je helemaal niks" (no "free"/money, even as a joke), cut the extra sportspullen sentence (one hook per pitch, don't stack them) and chose "in beweging" over "sterk". The date line in the mail has no location.

## Known facts for pitches
- Running since June 2026; record attendance: 10 participants (earlier max was 8). Do not use the record in pitches (Tim, 2026-11-18).
- Sport T-shirts: given to the most loyal participants; you get one after your 5th session.
