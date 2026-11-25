# Brand — T.A Vitality

Source of truth for all visual and written branding (approved by Tim, 2026-11-24). Visual version: `output/brand/brandbook_2026-11-24.html` (Tim chose this version back on 2026-11-24; v2 is archived in `output/brand/archief/`). Logo files: `knowledge/brand/logo/`.

## Story
Work and life are merging. Good employers take care of their people, and movement is the best way to break up or end a workday. Work is more than a paycheck — it is a way of living. T.A Vitality brings weekly movement to the workplace so people go to work with a good feeling.

## Values
- **Timeless** — calm shapes, few colours, lots of space.
- **A good product** — precise, quality without luxury.
- **Honest** — say what we do; no promises we cannot keep.

## Name
- Running text (mails, invoices, website copy): **T.A Vitality** — one dot, between T and A, none after A. This is deliberate (Tim's signature), not a typo.
- Logo, clothing, lowercase headings: **t.a vitality**.
- Never: "T.A. Vitality", "TA Vitality", "TAV", "T.A VITALITY".
- **Slogan:** "werk in beweging." — lowercase, always with the dot. Next to/under the logo, website closer, presentations. Never on clothing.

## Logo (concept B)
- Two overlapping circles = work and life; the red lens where they overlap = T.A Vitality.
- Geometry: radius 7x, stroke 1x, centre distance 8x (SVG: r 28, stroke 4, centres 32 apart). Lens always filled.
- Clear space: one circle radius around the logo. Minimum size: 16 px screen, 12 mm print, 25 mm embroidery.
- Files: `symbool_*` (symbol only), `logo_*` (symbol + wordmark), `logo-slogan_*`; colourways `kleur-op-licht`, `kleur-op-donker`, `eenkleur-inkt`, `eenkleur-wit`, `eenkleur-rood`.
- Wordmark uses live text (Inter Tight).
- Wordmark dot: red on light backgrounds; kalk/white on dark backgrounds, because red on inkt (2.4:1) makes the dot disappear (Tim, 2026-11-25). The red lens in the symbol stays red on dark. Before sending files to a printer or embroiderer, the text must be converted to outlines.
- Don't: rotate, stretch, add shadow/gradient, recolour the lens (only red, white or ink), fill the circles, add a third circle.

## Colours
| Name | Hex | RGB | CMYK (approx.) | Use |
|---|---|---|---|---|
| Vitality-rood | #A3302B | 163 48 43 | 0 71 74 36 | accent: lens, dot, buttons |
| Inkt | #1D1C1A | 29 28 26 | 0 3 10 89 | text, clothing |
| Kalk | #F3EFE8 | 243 239 232 | 0 2 5 5 | background, logo on dark |
| Steen | #6B655C | 107 101 92 | 0 6 14 58 | captions, lines |
| Blos | #E8CFC4 | 232 207 196 | 0 11 16 9 | soft surfaces, labels |

- Ratio: kalk ±60%, inkt ±25%, rood ±10%, blos ±5%.
- Contrast (WCAG): inkt on kalk 14.9, rood on kalk 6.1, steen on kalk 5.0. Rood on inkt is only 2.4 → on dark backgrounds use kalk for text and logo lines (the red lens may stay).
- CMYK values are calculated approximations; the printer/embroiderer matches #A3302B on a proof.

## Typography
- **Inter Tight** (Google Fonts, free) for headings and the wordmark: weight 600, slightly tight letter-spacing.
- **Inter** for body text, forms and buttons: weight 400/500.

## Graphic language
- Calm, timeless, product-design feel: lots of space, white cards with rounded corners (~18 px) on a kalk background, one red accent.
- Avoid: exuberant, gold, high-end luxury, gym/muscle imagery, gradients, emoji, shouting capitals, stock photos of smiling people in sportswear.

## Tone of voice
Businesslike, direct, honest. Address the client as **u**. Short sentences, most important first.
- Yes: "Eén keer per week 45 minuten bewegen, op uw eigen locatie." / "Wilt u kennismaken? Plan een gesprek van 15 minuten."
- No: "Transformeer je team NU!", "Dé nummer 1 in …", "ontzorgen", "holistisch", "journey".

## Clothing
- Clean, one colour, only the symbol, small on the back (centred, 4 cm below the collar, 6–8 cm wide). Front stays empty.
- Base colour ink; red only for one standout piece (e.g. hoodie). Logo white on ink/red, or ink on white.
- Never: slogan, large name, numbers, other logos.

## Website
- Kalk background, white cards, inkt text, red primary button; secondary button with red or inkt outline.
- Photos later: real sessions only, may be cropped in the lens shape. Favicon: kalk symbol on red.

### Website direction (Tim, 2026-11-25)
References Tim picked: **moooi.com** ("smooth, has an edge, something slow and calm, it moves and feels like a good product") and **uitpaulineskeuken.nl** ("clear, calm, well-organised").
- From Moooi: full-screen hero with one centred headline (Tim compared 500 vs 600 on 2026-11-25 and chose semi-bold 600 for "werk in beweging."), small uppercase kicker above it, small pill button; minimal header; slow motion with a long ease-out (cubic-bezier(0.19, 1, 0.22, 1), ~1–1.3 s); nothing jumps or flashes.
- From Uit Pauline's Keuken: calm warm background, centred section headings with one short intro line, clear categories, cards with small tags.
- Motion: slow and purposeful (the two logo circles drifting together), always respecting "reduce motion" settings. No autoplay sound, no parallax tricks.
- Later (Tim): the site grows into a place to browse — facts ("weetjes"), cases of what went well, more pages to click through. Build the structure so a menu and extra pages can be added without a redesign.
