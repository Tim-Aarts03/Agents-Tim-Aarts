"""Write a month ledger to Excel in Tim's existing 7-tab layout, plus the year overview.

Totals are live Excel formulas (like Tim's own files) so Tim can still edit a cell;
tools.bookkeeping computes the same numbers for the weekly report.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet

from tools.bookkeeping import (BOOK_DIR, DATA_DIR, Config, Ledger, PaymentMethod, due_date, given, kor_status,
                               month_label, rate_on, summarize, year_rows)

MONTH_DIR = BOOK_DIR / "Maandelijkse administratie"
CREATOR = "tools.bookkeeping"  # marks files this tool may overwrite
EUR = '€ #,##0.00'
DATE = 'DD-MM-YYYY'
BOLD = Font(bold=True)
TITLE = Font(bold=True, size=14)
HEADER_FILL = PatternFill("solid", fgColor="D9E1F2")


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
    if fmt:
        c.number_format = fmt
    elif isinstance(value, date):
        c.number_format = DATE
    return c


def _widths(ws: Worksheet, widths: dict[str, int]) -> None:
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def _income_expenses(wb: Workbook, ledger: Ledger, label: str) -> tuple[int, int]:
    ws = wb.create_sheet("Inkomsten en uitgaven")
    ws["B1"], ws["C1"] = "Inkomsten en uitgaven", label
    ws["B1"].font = TITLE
    _header(ws, 3, 2, ["Datum", "Factuurnummer", "Omschrijving", "Categorie", "Inkomsten", "Uitgaven",
                       "BTW-tarief", "BTW-bedrag", "Betaalwijze", "Status"])
    paid = {p.invoice for p in ledger.payments}
    rows = [(e.date, "", f"{e.description} – {e.shop}", e.category, 0, e.amount, e.payment_method.value, "Betaald")
            for e in ledger.expenses]
    rows += [(i.date, i.number, i.description, "INK-01 Omzet / Facturen", i.amount, 0,
              PaymentMethod.TRANSFER.value, "Betaald" if i.number in paid else "Open") for i in ledger.invoices]
    r = 4
    for d, nr, desc, cat, inc, exp, method, status in sorted(rows, key=lambda x: x[0]):
        for col, v in zip(range(2, 12), [d, nr, desc, cat, inc, exp, "Vrijgesteld", 0, method, status]):
            _put(ws, r, col, v, EUR if col in (6, 7, 9) else None)
        r += 1
    first, last = 4, max(r - 1, 4)
    tot = last + 2
    ws.cell(tot, 2, "Totaal").font = BOLD
    _put(ws, tot, 6, f"=SUM(F{first}:F{last})", EUR)
    _put(ws, tot, 7, f"=SUM(G{first}:G{last})", EUR)
    ws.cell(tot + 1, 2, "Netto resultaat").font = BOLD
    _put(ws, tot + 1, 6, f"=F{tot}-G{tot}", EUR)
    ws.cell(tot + 2, 2, "Waarvan nog niet ontvangen (Open)")
    _put(ws, tot + 2, 6, f'=SUMIF(K{first}:K{last},"Open",F{first}:F{last})', EUR)
    ws.cell(tot + 4, 2, "Alle uitgaven zijn inclusief BTW geboekt (KOR: vrijgesteld van BTW). "
                        "Datum = transactiedatum.")
    _widths(ws, {"B": 12, "C": 14, "D": 60, "E": 24, "F": 12, "G": 12, "H": 12, "I": 11, "J": 15, "K": 10})
    return tot, tot + 2


def _travel(wb: Workbook, ledger: Ledger, cfg: Config, label: str) -> int:
    ws = wb.create_sheet("Reiskosten")
    ws["B1"], ws["C1"] = "Reiskosten", label
    ws["B1"].font = TITLE
    _header(ws, 3, 2, ["Datum", "Locatie", "Vervoersmiddel", "Van (heen)", "Naar (heen)", "Van (terug)",
                       "Naar (terug)", "Karakter", "Kilometer", "Vergoeding"])
    sessions = given(ledger)
    first = 4
    for i, s in enumerate(sessions):
        r = first + i
        for col, v in zip(range(2, 10), [s.date, s.location or cfg.location, cfg.ride.vehicle, cfg.ride.origin,
                                         cfg.ride.destination, cfg.ride.destination, cfg.ride.origin, "Zakelijk"]):
            _put(ws, r, col, v)
        ws.cell(r, 10, "=$C$100")
        _put(ws, r, 11, f"=J{r}*$C$101", EUR)
    last = max(first + len(sessions) - 1, first)
    tot = last + 2
    ws.cell(tot, 2, "Totaal").font = BOLD
    ws.cell(tot, 10, f"=SUM(J{first}:J{last})")
    _put(ws, tot, 11, f"=SUM(K{first}:K{last})", EUR)
    ws.cell(tot + 1, 2, "Aantal ritten")
    ws.cell(tot + 1, 10, f"=COUNT(B{first}:B{last})")
    # assumptions far below the table so the table can grow without moving them
    ws["B99"] = "Aannames"
    ws["B99"].font = BOLD
    ws["B100"], ws["C100"] = "Km per rit (heen + terug)", cfg.ride.km_round_trip
    ws["B101"], ws["C101"] = "Tarief per km (€)", cfg.ride.rate_per_km
    ws.cell(tot + 3, 2, "Memo: nog NIET geboekt als kosten; eerst aftrekbaarheid bevestigen.")
    _widths(ws, {"B": 12, "C": 16, "D": 15, "E": 30, "F": 40, "G": 40, "H": 30, "I": 10, "J": 10, "K": 11})
    return tot


def _hours(wb: Workbook, ledger: Ledger, cfg: Config, label: str) -> tuple[int, int]:
    ws = wb.create_sheet("Urenregistratie")
    ws["C1"], ws["D1"] = "Urenregistratie", label
    ws["C1"].font = TITLE
    _header(ws, 3, 3, ["Datum", "Klant/project", "Omschrijving van de werkzaamheden", "Uren",
                       "Facturabel?", "Tarief (per sessie)"])
    r = 4
    for s in given(ledger):
        for desc, hours, billable in [("Reistijd heen (fiets) – niet facturabel", cfg.travel_hours_one_way, "Nee"),
                                      (f"Bootcamp sessie op locatie ({cfg.session_time})", cfg.session_hours, "Ja"),
                                      ("Reistijd terug (fiets) – niet facturabel", cfg.travel_hours_one_way, "Nee")]:
            for col, v in zip(range(3, 7), [s.date, cfg.client, desc, hours]):
                _put(ws, r, col, v)
            ws.cell(r, 7, billable)
            _put(ws, r, 8, rate_on(s.date, cfg) if billable == "Ja" else 0, EUR)
            r += 1
    first, last = 4, max(r - 1, 4)
    tot = last + 2
    ws.cell(tot, 3, "Totaal uren").font = BOLD
    ws.cell(tot, 6, f"=SUM(F{first}:F{last})")
    _put(ws, tot, 8, f"=SUM(H{first}:H{last})", EUR)
    ws.cell(tot + 1, 3, "Waarvan facturabel (uren)")
    ws.cell(tot + 1, 6, f'=SUMIF(G{first}:G{last},"Ja",F{first}:F{last})')
    ws.cell(tot + 2, 3, "Aantal sessies")
    ws.cell(tot + 2, 6, f'=COUNTIF(G{first}:G{last},"Ja")')
    _widths(ws, {"C": 12, "D": 20, "E": 48, "F": 8, "G": 11, "H": 18})
    return tot + 1, tot + 2


def _sessions(wb: Workbook, ledger: Ledger, cfg: Config, label: str) -> int:
    ws = wb.create_sheet("Sessies")
    ws["B1"] = f"Bootcamp-sessies & facturatie – {label}"
    ws["B1"].font = TITLE
    _header(ws, 3, 2, ["Datum", "Locatie", "Deelnemers", "Status", "Factuurnr", "Tarief"])
    invoiced = {d: i.number for i in ledger.invoices for d in i.sessions}
    first = 4
    for i, s in enumerate(sorted(ledger.sessions, key=lambda x: x.date)):
        r = first + i
        status = "Gegeven" if s.participants > 0 else "Geannuleerd"
        for col, v in zip(range(2, 7), [s.date, s.location or cfg.location, s.participants, status,
                                        invoiced.get(s.date, "")]):
            _put(ws, r, col, v)
        _put(ws, r, 7, rate_on(s.date, cfg) if status == "Gegeven" else 0, EUR)
    last = max(first + len(ledger.sessions) - 1, first)
    tot = last + 2
    ws.cell(tot, 2, "Gegeven sessies").font = BOLD
    ws.cell(tot, 5, f'=COUNTIF(E{first}:E{last},"Gegeven")')
    ws.cell(tot + 1, 2, "Waarde gegeven sessies")
    _put(ws, tot + 1, 5, f"=SUM(G{first}:G{last})", EUR)
    _widths(ws, {"B": 12, "C": 16, "D": 12, "E": 13, "F": 10, "G": 10})
    return tot


def _receipts(wb: Workbook, ledger: Ledger, label: str, expense_total_ref: str) -> int:
    ws = wb.create_sheet("Bonnen")
    ws["B1"] = f"Bonnen & bankcontrole – {label}"
    ws["B1"].font = TITLE
    _header(ws, 3, 2, ["Datum", "Winkel", "Bonbedrag", "Bank (afschrift)", "Verschil",
                       "BTW op bon (info)", "Betaalwijze", "Controle"])
    first = 4
    for i, e in enumerate(sorted(ledger.expenses, key=lambda x: x.date)):
        r = first + i
        for col, v, fmt in [(2, e.date, None), (3, e.shop, None), (4, e.amount, EUR), (5, e.bank_amount, EUR),
                            (7, e.vat_on_receipt, EUR), (8, e.payment_method.value, None)]:
            _put(ws, r, col, v, fmt)
        _put(ws, r, 6, f'=IF(E{r}="","",ROUND(D{r}-E{r},2))', EUR)
        note = e.bank_note or ("Contant: geen afschrift" if e.payment_method == PaymentMethod.CASH
                               else ("" if e.bank_amount is not None else "Afschrift nog niet bevestigd"))
        ws.cell(r, 9, note)
    last = max(first + len(ledger.expenses) - 1, first)
    tot = last + 2
    ws.cell(tot, 2, "Totaal").font = BOLD
    _put(ws, tot, 4, f"=SUM(D{first}:D{last})", EUR)
    ws.cell(tot + 2, 2, "Totaal bonnen vs. uitgaven in administratie")
    _put(ws, tot + 2, 6, f"=D{tot}-{expense_total_ref}", EUR)
    ws.cell(tot + 2, 7, f'=IF(ROUND(F{tot + 2},2)=0,"OK","CONTROLEER")')
    ws.cell(tot + 4, 2, "Bonnen volledig (incl. BTW) als kosten geboekt vanwege de KOR. Bonnen 7 jaar bewaren.")
    _widths(ws, {"B": 12, "C": 32, "D": 11, "E": 15, "F": 10, "G": 16, "H": 12, "I": 34})
    return tot + 2


def _carryover(wb: Workbook, ledger: Ledger, cfg: Config, label: str) -> tuple[int, int]:
    ws = wb.create_sheet("Overdracht")
    ws["B1"] = f"Overdracht – {label}"
    ws["B1"].font = TITLE
    ws["B2"] = "Openstaande posten die van maand naar maand doorlopen. Beginstand = eindstand vorige maand."
    s = summarize(ledger, cfg)
    r = 4

    def block(title: str, invoices, wip) -> tuple[int, int]:
        nonlocal r
        ws.cell(r, 2, title).font = BOLD
        r += 1
        ws.cell(r, 2, "A. Openstaande facturen")
        r += 1
        _header(ws, r, 2, ["Factuurnr", "Datum", "Klant", "Bedrag", "Vervaldatum"])
        r += 1
        a = r
        for inv in invoices:
            for col, v, fmt in [(2, inv.number, None), (3, inv.date, None), (4, inv.client, None),
                                (5, inv.amount, EUR), (6, due_date(inv, cfg), None)]:
                _put(ws, r, col, v, fmt)
            r += 1
        ws.cell(r, 2, "Totaal openstaande facturen").font = BOLD
        _put(ws, r, 5, f"=SUM(E{a}:E{max(r - 1, a)})" if invoices else 0, EUR)
        inv_total = r
        r += 2
        ws.cell(r, 2, "B. Onderhanden werk (gegeven, nog niet gefactureerd)")
        r += 1
        _header(ws, r, 2, ["Sessiedatum", "Omschrijving", "Klant", "Bedrag"])
        r += 1
        a = r
        for w in wip:
            for col, v, fmt in [(2, w.date, None), (3, "Bootcamp sessie", None), (4, w.client, None),
                                (5, w.amount, EUR)]:
                _put(ws, r, col, v, fmt)
            r += 1
        ws.cell(r, 2, "Totaal onderhanden werk").font = BOLD
        _put(ws, r, 5, f"=SUM(E{a}:E{max(r - 1, a)})" if wip else 0, EUR)
        wip_total = r
        r += 3
        return inv_total, wip_total

    block("BEGINSTAND (overgenomen uit vorige maand)", ledger.opening.open_invoices, ledger.opening.wip)
    end = block("EINDSTAND (naar volgende maand)", s.open_invoices_end, s.wip_end)
    _widths(ws, {"B": 28, "C": 16, "D": 22, "E": 12, "F": 13})
    return end


def build_month(ledger: Ledger, cfg: Config, out_dir: Path = MONTH_DIR, today: date | None = None,
                data_dir: Path = DATA_DIR) -> Path:
    path = out_dir / f"Administratie_{cfg.owner.replace(' ', '_')}_{ledger.month}.xlsx"
    _guard(path)
    label = month_label(ledger.month)
    s = summarize(ledger, cfg, today)
    wb = Workbook()
    wb.properties.creator = CREATOR
    ov = wb.active
    ov.title = "Overzicht"

    inc_tot, inc_open = _income_expenses(wb, ledger, label)
    travel_tot = _travel(wb, ledger, cfg, label)
    billable_ref, hour_sessions = _hours(wb, ledger, cfg, label)
    sess_tot = _sessions(wb, ledger, cfg, label)
    receipts_ok = _receipts(wb, ledger, label, f"'Inkomsten en uitgaven'!G{inc_tot}")
    inv_end, wip_end = _carryover(wb, ledger, cfg, label)

    ov["B1"] = f"{cfg.owner} – {cfg.business} – {label}"
    ov["B1"].font = TITLE
    ov["B2"] = "Gemaakt door de boekhoud-agent. Bedragen komen uit de andere tabbladen."
    _header(ov, 4, 2, ["Kerncijfers", "Waarde"])
    figures = [
        ("Totaal inkomsten (gefactureerd in deze maand)", f"='Inkomsten en uitgaven'!F{inc_tot}", EUR),
        ("   waarvan nog niet ontvangen", f"='Inkomsten en uitgaven'!F{inc_open}", EUR),
        ("Totaal uitgaven", f"='Inkomsten en uitgaven'!G{inc_tot}", EUR),
        ("Netto resultaat", f"='Inkomsten en uitgaven'!F{inc_tot + 1}", EUR),
        ("Aantal gegeven sessies", f"=Sessies!E{sess_tot}", None),
        ("Facturabele uren", f"=Urenregistratie!F{billable_ref}", None),
        ("Reiskosten fiets (memo – niet geboekt)", f"=Reiskosten!K{travel_tot}", EUR),
        ("Openstaande facturen einde maand", f"=Overdracht!E{inv_end}", EUR),
        ("Onderhanden werk einde maand (nog niet gefactureerd)", f"=Overdracht!E{wip_end}", EUR),
    ]
    for i, (name, formula, fmt) in enumerate(figures):
        ov.cell(5 + i, 2, name)
        _put(ov, 5 + i, 3, formula, fmt)
    _header(ov, 15, 2, ["Controles", "Resultaat"])
    checks = [
        ("Bonnen = uitgaven in administratie", f"=Bonnen!G{receipts_ok}"),
        ("Aantal sessies in uren = aantal ritten",
         f'=IF(Urenregistratie!F{hour_sessions}=Reiskosten!J{travel_tot + 1},"OK","CONTROLEER")'),
        ("Aantal sessies in uren = gegeven sessies",
         f'=IF(Urenregistratie!F{hour_sessions}=Sessies!E{sess_tot},"OK","CONTROLEER")'),
    ]
    for name, ok, detail in s.checks:
        checks.append((f"{name} ({detail})", "OK" if ok else "CONTROLEER"))
    for i, (name, value) in enumerate(checks):
        ov.cell(16 + i, 2, name)
        ov.cell(16 + i, 3, value)
    r = 17 + len(checks)
    ov.cell(r, 2, "Aandachtspunten").font = BOLD
    _, kor = kor_status(int(ledger.month[:4]), cfg, data_dir)
    for i, text in enumerate(s.attention + ledger.notes + [kor], start=1):
        ov.cell(r + i, 2, f"{i}. {text}")
    _widths(ov, {"B": 70, "C": 16})

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
    _header(ws, 4, 2, ["Maand", "Bestand", "Inkomsten", "Uitgaven", "Netto", "Sessies", "Facturabele uren",
                       "Reiskosten (memo)", "Open facturen einde maand", "Onderhanden werk einde maand", "Status"])
    for m in range(1, 13):
        r = 4 + m
        key = f"{year}-{m:02d}"
        ws.cell(r, 2, month_label(key).split()[0])
        row = rows.get(key)
        if row:
            for col, v, fmt in [(3, row.file, None), (4, row.income, EUR), (5, row.expenses, EUR),
                                (7, row.sessions, None), (8, row.billable_hours, None),
                                (9, row.travel_allowance, EUR), (10, row.open_invoices_end, EUR),
                                (11, row.wip_end, EUR), (12, row.status, None)]:
                _put(ws, r, col, v, fmt)
            _put(ws, r, 6, f"=D{r}-E{r}", EUR)
    ws.cell(17, 2, "Totaal jaar").font = BOLD
    for col in "DEFGHI":
        _put(ws, 17, ord(col) - 64, f"=SUM({col}5:{col}16)", None if col in "GH" else EUR)
    _, kor = kor_status(year, cfg, data_dir)
    ws["B19"] = kor
    _widths(ws, {"B": 12, "C": 38, "D": 12, "E": 12, "F": 12, "G": 9, "H": 15, "I": 16, "J": 22, "K": 26,
                 "L": 18})
    out_dir.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path
