"""Write a month ledger to Excel in Tim's own 7-tab layout, plus the year overview.

The layout copies Tim's hand-made November 2026 file: header row "owner | year | month",
data from row 4, totals below with one empty row inside the SUM range (so Tim can insert
a row), assumptions directly under each table, and his colour code (blue = input,
black = formula, green = link to another tab). tools.bookkeeping computes the same numbers
for the weekly report.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet

from tools.bookkeeping import (BOOK_DIR, DATA_DIR, MONTHS_NL, Config, Ledger, due_date, given, is_cash,
                               kor_status, month_label, summarize, year_rows)

MONTH_DIR = BOOK_DIR / "Maandelijkse administratie"
CREATOR = "tools.bookkeeping"  # marks files this tool may overwrite
EUR = '€ #,##0.00'
DATE = 'DD-MM-YYYY'
BOLD = Font(bold=True)
TITLE = Font(bold=True, size=14)
BLUE, GREEN = Font(color="0000FF"), Font(color="008000")
HEADER_FILL = PatternFill("solid", fgColor="D9E1F2")
COLOUR_NOTE = ("Kleurcode: blauw = invoer/aanname, zwart = formule, groen = koppeling naar ander tabblad, "
               "geel vlak = aan te passen cel.")


class NotOurs(Exception):
    pass


def _guard(path: Path) -> None:
    """Never overwrite Tim's hand-made files (July–October)."""
    if path.exists() and load_workbook(path).properties.creator != CREATOR:
        raise NotOurs(f"{path.name} was not made by this tool; refusing to overwrite")


def _header(ws: Worksheet, row: int, col: int, names: list[str]) -> None:
    for i, n in enumerate(names):
        c = ws.cell(row=row, column=col + i, value=n)
        c.font, c.fill = BOLD, HEADER_FILL


def _put(ws: Worksheet, row: int, col: int, value, fmt: str | None = None):
    c = ws.cell(row=row, column=col, value=value)
    if isinstance(value, str) and value.startswith("="):
        if "!" in value:
            c.font = GREEN
    elif value is not None:
        c.font = BLUE
    if fmt:
        c.number_format = fmt
    elif isinstance(value, date):
        c.number_format = DATE
    return c


def _label(ws: Worksheet, row: int, col: int, text: str, bold: bool = False):
    c = ws.cell(row=row, column=col, value=text)
    if bold:
        c.font = BOLD
    return c


def _title_row(ws: Worksheet, col: int, cfg: Config, month: str) -> None:
    y, m = map(int, month.split("-"))
    ws.cell(1, col, cfg.owner).font = TITLE
    ws.cell(1, col + 1, y).font = TITLE
    ws.cell(1, col + 2, MONTHS_NL[m - 1].capitalize()).font = TITLE


def _widths(ws: Worksheet, widths: dict[str, int]) -> None:
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def _span(first: int, n_rows: int) -> tuple[int, int, int]:
    """(last data row, last row inside SUM range incl. one spare row, totals row)."""
    last = first + max(n_rows, 1) - 1
    return last, last + 1, last + 2


def _income_expenses(wb: Workbook, ledger: Ledger, cfg: Config) -> int:
    ws = wb.create_sheet("Inkomsten en uitgaven")
    _title_row(ws, 2, cfg, ledger.month)
    _header(ws, 3, 2, ["Datum", "Factuurnummer", "Omschrijving", "Categorie", "Inkomsten", "Uitgaven",
                       "BTW-tarief", "BTW-bedrag", "Betaalwijze", "Status"])
    paid = {p.invoice for p in ledger.payments}
    rows = [(e.date, None, e.description, e.category, 0, e.amount, e.payment_method, e.status)
            for e in ledger.expenses]
    rows += [(i.date, i.number, i.description, "INK-01 Omzet / Facturen", i.amount, 0, "Overschrijving",
              "Betaald" if i.number in paid else "Open") for i in ledger.invoices]
    for r, (d, nr, desc, cat, inc, exp, method, status) in enumerate(sorted(rows, key=lambda x: x[0]), start=4):
        for col, v in zip(range(2, 12), [d, nr, desc, cat, inc, exp, "Vrijgesteld", 0, method, status]):
            _put(ws, r, col, v, EUR if col in (6, 7, 9) else None)
    _, end, tot = _span(4, len(rows))
    _label(ws, tot, 2, "Totaal", True)
    for col in "FGI":
        ws.cell(tot, ord(col) - 64, f"=SUM({col}4:{col}{end})").number_format = EUR
    _label(ws, tot + 1, 2, "Netto resultaat", True)
    ws.cell(tot + 1, 6, f"=F{tot}-G{tot}").number_format = EUR
    _label(ws, tot + 2, 2, "Waarvan nog niet ontvangen (Open)")
    ws.cell(tot + 2, 6, f'=SUMIF(K4:K{end},"Open",F4:F{end})').number_format = EUR
    _label(ws, tot + 4, 2, "Alle uitgaven zijn inclusief BTW geboekt (ondernemer is vrijgesteld van BTW). "
                           "BTW-tarief altijd 'Vrijgesteld', BTW-bedrag 0. Datum = transactiedatum.")
    _widths(ws, {"B": 12, "C": 14, "D": 70, "E": 34, "F": 12, "G": 12, "H": 12, "I": 11, "J": 30, "K": 24})
    return tot


def _travel(wb: Workbook, ledger: Ledger, cfg: Config) -> int:
    ws = wb.create_sheet("Reiskosten")
    _title_row(ws, 2, cfg, ledger.month)
    _header(ws, 3, 2, ["Datum", "Locatie", "Vervoersmiddel", "Van (heen)", "Naar (heen)", "Van (terug)",
                       "Naar (terug)", "Karakter", "Kilometer", "Vergoeding"])
    sessions = given(ledger)
    last, _, _ = _span(4, len(sessions))
    tot = last + 1
    km_row, rate_row = tot + 4, tot + 5
    for r, s in enumerate(sessions, start=4):
        for col, v in zip(range(2, 10), [s.date, s.location or cfg.location, cfg.ride.vehicle, cfg.ride.origin,
                                         cfg.ride.destination, cfg.ride.destination, cfg.ride.origin, "Zakelijk"]):
            _put(ws, r, col, v)
        ws.cell(r, 10, f"=$C${km_row}")
        ws.cell(r, 11, f"=J{r}*$C${rate_row}").number_format = EUR
    _label(ws, tot, 2, "Totaal", True)
    ws.cell(tot, 10, f"=SUM(J4:J{last})")
    ws.cell(tot, 11, f"=SUM(K4:K{last})").number_format = EUR
    _label(ws, tot + 1, 2, "Aantal ritten")
    ws.cell(tot + 1, 10, f"=COUNTA(B4:B{last})")
    _label(ws, tot + 3, 2, "Aannames", True)
    _label(ws, km_row, 2, "Km per rit (heen + terug)")
    _put(ws, km_row, 3, cfg.ride.km_round_trip)
    _label(ws, rate_row, 2, "Tarief per km (€)")
    _put(ws, rate_row, 3, cfg.ride.rate_per_km)
    _label(ws, rate_row + 2, 2, "Let op: deze vergoeding is nog NIET geboekt op 'Inkomsten en uitgaven' – eerst "
                                "aftrekbaarheid bevestigen. Ritten blijven bijhouden als onderbouwing.")
    _widths(ws, {"B": 26, "C": 16, "D": 15, "E": 30, "F": 45, "G": 45, "H": 30, "I": 10, "J": 10, "K": 11})
    return tot


def _hours(wb: Workbook, ledger: Ledger, cfg: Config) -> tuple[int, int, str]:
    """Returns (billable-hours row, session-count row, rate lookup formula template)."""
    ws = wb.create_sheet("Urenregistratie")
    _title_row(ws, 3, cfg, ledger.month)
    _header(ws, 3, 3, ["Datum", "Klant/project", "Omschrijving van de werkzaamheden", "Begintijd", "Eindtijd",
                       "Pauze", "Totaal aantal uren", "Facturabel?", "Tarief (per sessie)"])
    start, travel = cfg.session_start, cfg.travel_hours_one_way
    end = start + cfg.session_hours
    blocks = [("Reistijd heen (fiets) – niet facturabel", start - travel, start, "Nee"),
              (f"Bootcamp sessie op locatie ({cfg.session_time})", start, end, "Ja"),
              ("Reistijd terug (fiets) – niet facturabel", end, end + travel, "Nee")]
    last, _, _ = _span(4, 3 * len(given(ledger)))
    tot = last + 1
    first_rate = tot + 6
    last_rate = first_rate + len(cfg.rates) - 1
    lookup = (f"LOOKUP({{date}},Urenregistratie!$J${first_rate}:$J${last_rate},"
              f"Urenregistratie!$K${first_rate}:$K${last_rate})")
    r = 4
    for s in given(ledger):
        for desc, t0, t1, billable in blocks:
            for col, v in zip(range(3, 9), [s.date, cfg.short, desc, round(t0, 2), round(t1, 2), 0]):
                _put(ws, r, col, v)
            ws.cell(r, 9, f"=G{r}-F{r}-H{r}")
            _put(ws, r, 10, billable)
            ws.cell(r, 11, f'=IF(J{r}="Ja",{lookup.format(date=f"C{r}")},0)').number_format = EUR
            r += 1
    _label(ws, tot, 3, "Totaal uren", True)
    ws.cell(tot, 9, f"=SUM(I4:I{last})")
    ws.cell(tot, 11, f"=SUM(K4:K{last})").number_format = EUR
    _label(ws, tot + 1, 3, "Waarvan facturabel (uren)")
    ws.cell(tot + 1, 9, f'=SUMIF(J4:J{last},"Ja",I4:I{last})')
    _label(ws, tot + 2, 3, "Aantal sessies")
    ws.cell(tot + 2, 9, f'=COUNTIF(J4:J{last},"Ja")')
    _label(ws, tot + 5, 3, "Aannames", True)
    for i, rate in enumerate(sorted(cfg.rates, key=lambda x: x.valid_from)):
        _label(ws, first_rate + i, 3, f"Tarief per sessie vanaf {rate.valid_from:%d-%m-%Y} (€)")
        _put(ws, first_rate + i, 10, rate.valid_from)
        _put(ws, first_rate + i, 11, rate.amount, EUR)
    hrs = lambda x: f"{x:.2f}".replace(".", ",")
    _label(ws, last_rate + 2, 3,
           f"Tijden zijn decimale uren (16,25 = 16:15). Alle sessies zijn gelijk: {hrs(cfg.session_hours)} uur les "
           f"({cfg.session_time}, facturabel) + {hrs(travel)} uur reistijd per enkele reis (niet facturabel). "
           "Alleen gegeven sessies.")
    _widths(ws, {"C": 12, "D": 14, "E": 48, "F": 10, "G": 10, "H": 7, "I": 17, "J": 12, "K": 18})
    return tot + 1, tot + 2, lookup


def _sessions(wb: Workbook, ledger: Ledger, cfg: Config, lookup: str) -> int:
    ws = wb.create_sheet("Sessies")
    ws["B1"] = f"Bootcamp-sessies & facturatie – {month_label(ledger.month).lower()}"
    ws["B1"].font = TITLE
    _header(ws, 3, 2, ["Datum", "Locatie", "Deelnemers", "Cijfer", "Status", "Factuurnr", "Tarief"])
    invoiced = {d: i.number for i in ledger.invoices for d in i.sessions}
    sessions = sorted(ledger.sessions, key=lambda x: x.date)
    last, _, _ = _span(4, len(sessions))
    for r, s in enumerate(sessions, start=4):
        for col, v in [(2, s.date), (3, s.location or cfg.location), (4, s.participants), (5, s.rating),
                       (7, invoiced.get(s.date))]:
            _put(ws, r, col, v)
        if s.participants is None:  # given, number unknown: the formula would say "Geannuleerd"
            _put(ws, r, 6, "Gegeven")
        else:
            ws.cell(r, 6, f'=IF(D{r}>0,"Gegeven","Geannuleerd")')
        ws.cell(r, 8, f'=IF(F{r}="Gegeven",{lookup.format(date=f"B{r}")},0)').number_format = EUR
    tot = last + 2
    _label(ws, tot - 1, 2, "Samenvatting", True)
    _label(ws, tot, 2, "Gegeven sessies")
    ws.cell(tot, 5, f'=COUNTIF(F4:F{last},"Gegeven")')
    _label(ws, tot + 1, 2, "Waarde gegeven sessies")
    ws.cell(tot + 1, 5, f"=SUM(H4:H{last})").number_format = EUR
    _label(ws, tot + 2, 2, "Daarvan op een factuur")
    ws.cell(tot + 2, 5, f'=SUMPRODUCT((F4:F{last}="Gegeven")*(G4:G{last}<>"")*H4:H{last})').number_format = EUR
    _label(ws, tot + 3, 2, "Nog niet op een factuur")
    ws.cell(tot + 3, 5, f'=SUMPRODUCT((F4:F{last}="Gegeven")*(G4:G{last}="")*H4:H{last})').number_format = EUR
    if cfg.contract:
        c = cfg.contract
        _label(ws, tot + 5, 2, f"Sessies vanaf {c.start:%d-%m} vallen onder het contract (€ {c.rate:.0f} per les, "
                               f"{c.sessions} lessen t/m {c.end:%d-%m}, factuur achteraf).")
    _widths(ws, {"B": 22, "C": 16, "D": 12, "E": 10, "F": 13, "G": 10, "H": 10})
    return tot


def _receipts(wb: Workbook, ledger: Ledger, expense_total_ref: str) -> int:
    ws = wb.create_sheet("Bonnen")
    ws["B1"] = f"Bonnen & bankcontrole – {month_label(ledger.month).lower()}"
    ws["B1"].font = TITLE
    _header(ws, 3, 2, ["Datum", "Winkel", "Bonbedrag", "Bank (afschrift)", "Verschil",
                       "BTW op bon (info)", "Betaalwijze", "Controle"])
    expenses = sorted(ledger.expenses, key=lambda x: x.date)
    _, end, tot = _span(4, len(expenses))
    for r, e in enumerate(expenses, start=4):
        for col, v, fmt in [(2, e.date, None), (3, e.shop, None), (4, e.amount, EUR), (5, e.bank_amount, EUR),
                            (7, e.vat_on_receipt, EUR), (8, e.payment_method, None)]:
            _put(ws, r, col, v, fmt)
        ws.cell(r, 6, f'=IF(E{r}="","",ROUND(D{r}-E{r},2))').number_format = EUR
        note = e.bank_note or ("Contant: geen afschrift" if is_cash(e)
                               else ("" if e.bank_amount is not None else "Afschrift nog niet bevestigd"))
        _put(ws, r, 9, note or None)
    _label(ws, tot, 2, "Totaal", True)
    ws.cell(tot, 4, f"=SUM(D4:D{end})").number_format = EUR
    ws.cell(tot, 7, f"=SUM(G4:G{end})").number_format = EUR
    _label(ws, tot + 2, 2, "Totaal bonnen vs. uitgaven in administratie")
    _put(ws, tot + 2, 6, f"=D{tot}-{expense_total_ref}", EUR)
    ws.cell(tot + 2, 7, f'=IF(ROUND(F{tot + 2},2)=0,"OK","CONTROLEER")')
    _label(ws, tot + 4, 2, "Alle bonnen zijn volledig (incl. BTW) als kosten geboekt vanwege de BTW-vrijstelling. "
                           "Bonnen 7 jaar bewaren.")
    _widths(ws, {"B": 12, "C": 40, "D": 11, "E": 15, "F": 10, "G": 16, "H": 22, "I": 70})
    return tot + 2


def _carryover(wb: Workbook, ledger: Ledger, cfg: Config, today: date) -> tuple[int, int]:
    ws = wb.create_sheet("Overdracht")
    ws["B1"] = f"Overdracht – {month_label(ledger.month).lower()}" + ("" if ledger.closed else " (voorlopig)")
    ws["B1"].font = TITLE
    ws["B2"] = "Openstaande posten die van maand naar maand doorlopen. Beginstand = eindstand vorige maand."
    s = summarize(ledger, cfg, today)
    paid = {p.invoice for p in ledger.payments}
    r = 4

    def remark(inv) -> str:
        due = due_date(inv, cfg)
        text = f"Verstuurd, factuurdatum {inv.date:%d-%m-%Y}"
        if inv.number in paid:
            return text + "; ontvangen"
        return text + (f"; vervallen {due:%d-%m}; nog niet ontvangen" if due < today else f"; vervalt {due:%d-%m}")

    def block(title: str, invoices, wip) -> tuple[int, int]:
        nonlocal r
        _label(ws, r, 2, title, True)
        _label(ws, r + 1, 2, "A. Openstaande facturen")
        _header(ws, r + 2, 2, ["Factuurnr", "Datum", "Klant", "Bedrag", "Vervaldatum", "Opmerking"])
        first = r + 3
        for i, inv in enumerate(invoices):
            for col, v, fmt in [(2, inv.number, None), (3, inv.date, None), (4, inv.client, None),
                                (5, inv.amount, EUR), (6, due_date(inv, cfg), None), (7, remark(inv), None)]:
                _put(ws, first + i, col, v, fmt)
        _, end, tot = _span(first, len(invoices))
        _label(ws, tot, 2, "Totaal openstaande facturen", True)
        ws.cell(tot, 5, f"=SUM(E{first}:E{end})").number_format = EUR
        inv_total = tot
        _label(ws, tot + 2, 2, "B. Onderhanden werk (gegeven, nog niet gefactureerd)")
        _header(ws, tot + 3, 2, ["Sessiedatum", "Omschrijving", "Klant", "Bedrag"])
        first = tot + 4
        for i, w in enumerate(wip):
            for col, v, fmt in [(2, w.date, None), (3, "Bootcamp sessie", None), (4, cfg.short, None),
                                (5, w.amount, EUR)]:
                _put(ws, first + i, col, v, fmt)
        _, end, tot = _span(first, len(wip))
        _label(ws, tot, 2, "Totaal onderhanden werk", True)
        ws.cell(tot, 5, f"=SUM(E{first}:E{end})").number_format = EUR
        r = tot + 3
        return inv_total, tot

    block("BEGINSTAND (overgenomen uit vorige maand)", ledger.opening.open_invoices, ledger.opening.wip)
    end = block(f"EINDSTAND (naar volgende maand) – stand per {today:%d-%m-%Y}", s.open_invoices_end, s.wip_end)
    _widths(ws, {"B": 30, "C": 16, "D": 22, "E": 12, "F": 13, "G": 70})
    return end


def build_month(ledger: Ledger, cfg: Config, out_dir: Path = MONTH_DIR, today: date | None = None,
                data_dir: Path = DATA_DIR) -> Path:
    today = today or date.today()
    path = out_dir / f"Administratie_{cfg.owner.replace(' ', '_')}_{ledger.month}.xlsx"
    _guard(path)
    s = summarize(ledger, cfg, today)
    wb = Workbook()
    wb.properties.creator = CREATOR
    ov = wb.active
    ov.title = "Overzicht"

    inc_tot = _income_expenses(wb, ledger, cfg)
    travel_tot = _travel(wb, ledger, cfg)
    billable_row, hour_sessions, lookup = _hours(wb, ledger, cfg)
    sess_tot = _sessions(wb, ledger, cfg, lookup)
    receipts_ok = _receipts(wb, ledger, f"'Inkomsten en uitgaven'!G{inc_tot}")
    inv_end, wip_end = _carryover(wb, ledger, cfg, today)

    ov["B1"] = (f"{cfg.owner} – {cfg.business} – {month_label(ledger.month)}"
                + ("" if ledger.closed else " (voorlopig)"))
    ov["B1"].font = TITLE
    ov["B2"] = ("Alle bedragen komen uit de andere tabbladen. Schone start per maand; "
                "openstaande posten staan in 'Overdracht'.")
    _header(ov, 4, 2, ["Kerncijfers", "Waarde"])
    figures = [
        ("Totaal inkomsten (gefactureerd in deze maand)", f"='Inkomsten en uitgaven'!F{inc_tot}", EUR),
        ("   waarvan nog niet ontvangen", f"='Inkomsten en uitgaven'!F{inc_tot + 2}", EUR),
        ("Totaal uitgaven", f"='Inkomsten en uitgaven'!G{inc_tot}", EUR),
        ("Netto resultaat", f"='Inkomsten en uitgaven'!F{inc_tot + 1}", EUR),
        ("Aantal gegeven sessies", f"=Sessies!E{sess_tot}", None),
        ("Facturabele uren", f"=Urenregistratie!I{billable_row}", None),
        ("Reiskosten fiets (memo – niet geboekt)", f"=Reiskosten!K{travel_tot}", EUR),
        ("Openstaande facturen einde maand", f"=Overdracht!E{inv_end}", EUR),
        ("Onderhanden werk einde maand (nog niet gefactureerd)", f"=Overdracht!E{wip_end}", EUR),
    ]
    for i, (name, formula, fmt) in enumerate(figures):
        _label(ov, 5 + i, 2, name)
        _put(ov, 5 + i, 3, formula, fmt)
    _header(ov, 15, 2, ["Controles", "Resultaat"])
    checks = [
        ("Bonnen = uitgaven in administratie", f"=Bonnen!G{receipts_ok}"),
        ("Aantal sessies in uren = aantal ritten",
         f'=IF(Urenregistratie!I{hour_sessions}=Reiskosten!J{travel_tot + 1},"OK","CONTROLEER")'),
        ("Aantal sessies in uren = gegeven sessies",
         f'=IF(Urenregistratie!I{hour_sessions}=Sessies!E{sess_tot},"OK","CONTROLEER")'),
    ] + [(f"{name} ({detail})", "OK" if ok else "CONTROLEER") for name, ok, detail in s.checks]
    for i, (name, value) in enumerate(checks):
        _label(ov, 16 + i, 2, name)
        _put(ov, 16 + i, 3, value)
    r = 17 + len(checks)
    _label(ov, r, 2, "Aandachtspunten", True)
    _, kor = kor_status(int(ledger.month[:4]), cfg, data_dir)
    items = s.attention + ledger.notes + [kor]
    for i, text in enumerate(items, start=1):
        _label(ov, r + i, 2, f"{i}. {text}")
    _label(ov, r + len(items) + 2, 2, COLOUR_NOTE)
    _widths(ov, {"B": 110, "C": 16})

    out_dir.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def build_year(year: int, cfg: Config, out_dir: Path = MONTH_DIR, data_dir: Path = DATA_DIR) -> Path:
    path = out_dir / f"Jaaroverzicht_{cfg.owner.replace(' ', '_')}_{year}.xlsx"
    if path.exists() and load_workbook(path).properties.creator != CREATOR:
        # keep Tim's hand-made version next to the generated one instead of overwriting it
        path.rename(path.with_name(path.stem + "_origineel.xlsx"))
    rows = {r.month: r for r in year_rows(year, cfg, data_dir)}
    wb = Workbook()
    wb.properties.creator = CREATOR
    ws = wb.active
    ws.title = f"Jaaroverzicht {year}"
    ws["B1"] = f"{cfg.owner} – {cfg.business} – Jaaroverzicht {year}"
    ws["B1"].font = TITLE
    ws["B2"] = "Eén regel per maand. Bestanden staan in dezelfde map."
    _header(ws, 4, 2, ["Maand", "Bestand", "Inkomsten", "Uitgaven", "Netto", "Sessies", "Facturabele uren",
                       "Reiskosten (memo)", "Open facturen einde maand", "Onderhanden werk einde maand", "Status"])
    for m in range(1, 13):
        r = 4 + m
        _label(ws, r, 2, MONTHS_NL[m - 1].capitalize())
        row = rows.get(f"{year}-{m:02d}")
        if row:
            for col, v, fmt in [(3, row.file, None), (4, row.income, EUR), (5, row.expenses, EUR),
                                (7, row.sessions, None), (8, row.billable_hours, None),
                                (9, row.travel_allowance, EUR), (10, row.open_invoices_end, EUR),
                                (11, row.wip_end, EUR), (12, row.status, None)]:
                _put(ws, r, col, v, fmt)
            ws.cell(r, 6, f"=D{r}-E{r}").number_format = EUR
    _label(ws, 17, 2, "Totaal jaar", True)
    for col in "DEFGHI":
        c = ws.cell(17, ord(col) - 64, f"=SUM({col}5:{col}16)")
        if col not in "GH":
            c.number_format = EUR
    _, kor = kor_status(year, cfg, data_dir)
    ws["B19"] = kor
    ws["B21"] = COLOUR_NOTE
    _widths(ws, {"B": 12, "C": 38, "D": 12, "E": 12, "F": 12, "G": 9, "H": 15, "I": 16, "J": 22, "K": 26,
                 "L": 18})
    out_dir.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path
