"""Bookkeeping for T.A Vitality: one JSON ledger per month, all arithmetic here.

The JSON ledger in `Boekhouding/data/` is the source of truth; the monthly Excel
file in Tim's own layout is generated from it (tools.bookkeeping_xlsx). The LLM
agent only turns Tim's Wednesday message into `add` commands.

Usage:
    python -m tools.bookkeeping init 2026-11
    python -m tools.bookkeeping add 2026-11 expense '{"date": "2026-11-17", ...}'
    python -m tools.bookkeeping report 2026-11 [--today 2026-11-19] [--out path.md]
    python -m tools.bookkeeping build 2026-11      # monthly xlsx + year overview
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

BOOK_DIR = Path("Boekhouding")
DATA_DIR = BOOK_DIR / "data"
CONFIG_FILE = Path("knowledge/private_bookkeeping.json")

MONTHS_NL = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
             "augustus", "september", "oktober", "november", "december"]


class Rate(BaseModel):
    valid_from: date
    amount: float


class Ride(BaseModel):
    vehicle: str
    origin: str
    destination: str
    km_round_trip: float
    rate_per_km: float


class Config(BaseModel):
    owner: str
    business: str
    client: str
    location: str
    rates: list[Rate]
    session_time: str  # e.g. "16:15–17:00"
    session_hours: float
    travel_hours_one_way: float
    ride: Ride
    payment_term_days: int = 14
    kor_threshold: float = 20000.0
    kor_warn_fraction: float = 0.75


class PaymentMethod(str, Enum):
    PIN = "Pin"
    CASH = "Contant"
    TRANSFER = "Overschrijving"
    IDEAL = "iDEAL"


class Expense(BaseModel):
    date: date
    description: str
    shop: str
    amount: float = Field(gt=0)
    payment_method: PaymentMethod = PaymentMethod.PIN
    category: str = "UIT-01 Inkoopgoederen"
    vat_on_receipt: float | None = None  # info only: KOR, so VAT is part of the cost
    bank_amount: float | None = None
    bank_note: str = ""


class Session(BaseModel):
    date: date
    participants: int = Field(ge=0)  # 0 = cancelled
    location: str | None = None


class Invoice(BaseModel):
    number: str
    date: date
    client: str
    description: str
    amount: float = Field(gt=0)
    sessions: list[date] = []  # work-in-progress sessions this invoice settles
    due_date: date | None = None


class Payment(BaseModel):
    invoice: str
    date: date
    amount: float = Field(gt=0)


class WipItem(BaseModel):
    date: date
    client: str
    amount: float


class Opening(BaseModel):
    open_invoices: list[Invoice] = []
    wip: list[WipItem] = []


class Ledger(BaseModel):
    month: str  # YYYY-MM
    opening: Opening = Opening()
    expenses: list[Expense] = []
    sessions: list[Session] = []
    invoices: list[Invoice] = []
    payments: list[Payment] = []
    notes: list[str] = []


class YearRow(BaseModel):
    """Month summary taken over from Tim's old (pre-tool) Excel files."""
    month: str
    file: str
    income: float
    expenses: float
    sessions: int
    billable_hours: float
    travel_allowance: float
    open_invoices_end: float
    wip_end: float
    status: str


class InvalidEntry(Exception):
    pass


# ---------- storage ----------

def load_config(path: Path = CONFIG_FILE) -> Config:
    return Config.model_validate_json(path.read_text())


def ledger_path(month: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"{month}.json"


def load_ledger(month: str, data_dir: Path = DATA_DIR) -> Ledger:
    return Ledger.model_validate_json(ledger_path(month, data_dir).read_text())


def save_ledger(ledger: Ledger, data_dir: Path = DATA_DIR) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    path = ledger_path(ledger.month, data_dir)
    path.write_text(ledger.model_dump_json(indent=2) + "\n")
    return path


def load_history(year: int, data_dir: Path = DATA_DIR) -> list[YearRow]:
    path = data_dir / f"history_{year}.json"
    if not path.exists():
        return []
    return [YearRow.model_validate(r) for r in json.loads(path.read_text())]


def previous_month(month: str) -> str:
    y, m = map(int, month.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def month_of(d: date) -> str:
    return f"{d.year}-{d.month:02d}"


def month_label(month: str) -> str:
    y, m = map(int, month.split("-"))
    return f"{MONTHS_NL[m - 1].capitalize()} {y}"


# ---------- rules ----------

def rate_on(d: date, cfg: Config) -> float:
    valid = [r for r in cfg.rates if r.valid_from <= d]
    if not valid:
        raise InvalidEntry(f"no session rate known for {d}")
    return max(valid, key=lambda r: r.valid_from).amount


def due_date(inv: Invoice, cfg: Config) -> date:
    return inv.due_date or inv.date + timedelta(days=cfg.payment_term_days)


def given(ledger: Ledger) -> list[Session]:
    return sorted((s for s in ledger.sessions if s.participants > 0), key=lambda s: s.date)


def init_month(month: str, cfg: Config, data_dir: Path = DATA_DIR) -> Ledger:
    """New month with the previous month's closing items as opening balance."""
    if ledger_path(month, data_dir).exists():
        raise InvalidEntry(f"{month} already exists")
    prev = ledger_path(previous_month(month), data_dir)
    ledger = Ledger(month=month)
    if prev.exists():
        s = summarize(Ledger.model_validate_json(prev.read_text()), cfg)
        ledger.opening = Opening(open_invoices=s.open_invoices_end, wip=s.wip_end)
    save_ledger(ledger, data_dir)
    return ledger


EntryKind = Literal["expense", "session", "invoice", "payment", "note", "opening_invoice", "opening_wip"]


def add_entry(ledger: Ledger, kind: EntryKind, data: dict | str, cfg: Config) -> Ledger:
    """Validate one entry and append it; refuse duplicates and wrong months."""
    def in_month(d: date) -> None:
        if month_of(d) != ledger.month:
            raise InvalidEntry(f"{d} is not in {ledger.month}")

    if kind == "note":
        ledger.notes.append(str(data))
    elif kind == "expense":
        e = Expense.model_validate(data)
        in_month(e.date)
        if any((x.date, x.amount, x.shop) == (e.date, e.amount, e.shop) for x in ledger.expenses):
            raise InvalidEntry(f"duplicate expense {e.date} {e.shop} {e.amount}")
        ledger.expenses.append(e)
    elif kind == "session":
        s = Session.model_validate(data)
        in_month(s.date)
        if any(x.date == s.date for x in ledger.sessions):
            raise InvalidEntry(f"session {s.date} already recorded")
        rate_on(s.date, cfg)
        ledger.sessions.append(s)
    elif kind == "invoice":
        inv = Invoice.model_validate(data)
        in_month(inv.date)
        if inv.number in {i.number for i in ledger.invoices + ledger.opening.open_invoices}:
            raise InvalidEntry(f"invoice {inv.number} already exists")
        ledger.invoices.append(inv)
    elif kind == "payment":
        p = Payment.model_validate(data)
        in_month(p.date)
        known = {i.number for i in ledger.invoices + ledger.opening.open_invoices}
        if p.invoice not in known:
            raise InvalidEntry(f"unknown invoice {p.invoice}")
        if any(x.invoice == p.invoice for x in ledger.payments):
            raise InvalidEntry(f"invoice {p.invoice} already paid")
        ledger.payments.append(p)
    elif kind == "opening_invoice":
        ledger.opening.open_invoices.append(Invoice.model_validate(data))
    elif kind == "opening_wip":
        ledger.opening.wip.append(WipItem.model_validate(data))
    else:
        raise InvalidEntry(f"unknown kind {kind}")
    return ledger


# ---------- summary ----------

class Summary(BaseModel):
    month: str
    income: float  # invoiced this month
    unpaid_of_income: float
    received: float
    expenses: float
    net: float
    sessions_given: int
    sessions_cancelled: int
    billable_hours: float
    total_hours: float
    rides: int
    travel_km: float
    travel_allowance: float
    session_value: float
    open_invoices_end: list[Invoice]
    wip_end: list[WipItem]
    checks: list[tuple[str, bool, str]]  # (name, ok, detail)
    attention: list[str]


def eur(x: float) -> str:
    """Dutch notation: € 1.234,56."""
    return "€ " + f"{x:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _r(x: float) -> float:
    return round(x + 0.0, 2)


def summarize(ledger: Ledger, cfg: Config, today: date | None = None) -> Summary:
    today = today or date.today()
    sessions = given(ledger)
    paid = {p.invoice for p in ledger.payments}
    income = sum(i.amount for i in ledger.invoices)
    expenses = sum(e.amount for e in ledger.expenses)

    open_end = [i for i in ledger.opening.open_invoices + ledger.invoices if i.number not in paid]
    settled = {d for i in ledger.invoices for d in i.sessions}
    new_wip = [WipItem(date=s.date, client=cfg.client, amount=rate_on(s.date, cfg)) for s in sessions]
    wip_end = sorted((w for w in ledger.opening.wip + new_wip if w.date not in settled), key=lambda w: w.date)

    checks: list[tuple[str, bool, str]] = []
    for e in ledger.expenses:
        if e.bank_amount is not None:
            diff = _r(e.amount - e.bank_amount)
            checks.append((f"Bon {e.date:%d-%m} {e.shop} = bank", diff == 0, f"verschil {eur(diff)}"))
    wip_dates = {w.date: w.amount for w in ledger.opening.wip + new_wip}
    for inv in ledger.invoices:
        if inv.sessions:
            missing = [d for d in inv.sessions if d not in wip_dates]
            expected = sum(wip_dates.get(d, 0) for d in inv.sessions)
            ok = not missing and _r(expected) == _r(inv.amount)
            detail = f"sessies {eur(expected)}, factuur {eur(inv.amount)}"
            if missing:
                detail += "; onbekende sessies: " + ", ".join(f"{d:%d-%m}" for d in missing)
            checks.append((f"Factuur {inv.number} = sessies × tarief", ok, detail))
    for p in ledger.payments:
        inv = next(i for i in ledger.opening.open_invoices + ledger.invoices if i.number == p.invoice)
        checks.append((f"Ontvangst factuur {p.invoice} = factuurbedrag", _r(p.amount) == _r(inv.amount),
                       f"ontvangen {eur(p.amount)}, factuur {eur(inv.amount)}"))

    attention: list[str] = []
    for inv in open_end:
        due = due_date(inv, cfg)
        if due < today:
            attention.append(f"Factuur {inv.number} ({eur(inv.amount)}, {inv.client}) is vervallen op "
                             f"{due:%d-%m-%Y} en nog niet ontvangen: betalingsherinnering overwegen.")
    for e in ledger.expenses:
        if e.payment_method != PaymentMethod.CASH and e.bank_amount is None:
            attention.append(f"Bon {e.date:%d-%m} {e.shop} ({eur(e.amount)}): nog niet bevestigd met bankafschrift.")

    return Summary(
        month=ledger.month,
        income=_r(income),
        unpaid_of_income=_r(sum(i.amount for i in ledger.invoices if i.number not in paid)),
        received=_r(sum(p.amount for p in ledger.payments)),
        expenses=_r(expenses),
        net=_r(income - expenses),
        sessions_given=len(sessions),
        sessions_cancelled=len(ledger.sessions) - len(sessions),
        billable_hours=_r(len(sessions) * cfg.session_hours),
        total_hours=_r(len(sessions) * (cfg.session_hours + 2 * cfg.travel_hours_one_way)),
        rides=len(sessions),
        travel_km=_r(len(sessions) * cfg.ride.km_round_trip),
        travel_allowance=_r(len(sessions) * cfg.ride.km_round_trip * cfg.ride.rate_per_km),
        session_value=_r(sum(w.amount for w in new_wip)),
        open_invoices_end=open_end,
        wip_end=wip_end,
        checks=checks,
        attention=attention,
    )


def year_rows(year: int, cfg: Config, data_dir: Path = DATA_DIR) -> list[YearRow]:
    """Old months from history, newer months computed from their ledgers."""
    rows = {r.month: r for r in load_history(year, data_dir)}
    for path in sorted(data_dir.glob(f"{year}-??.json")):
        s = summarize(Ledger.model_validate_json(path.read_text()), cfg)
        rows[s.month] = YearRow(
            month=s.month, file=f"Administratie_{cfg.owner.replace(' ', '_')}_{s.month}.xlsx",
            income=s.income, expenses=s.expenses, sessions=s.sessions_given,
            billable_hours=s.billable_hours, travel_allowance=s.travel_allowance,
            open_invoices_end=_r(sum(i.amount for i in s.open_invoices_end)),
            wip_end=_r(sum(w.amount for w in s.wip_end)), status="Via agent")
    return [rows[m] for m in sorted(rows)]


def kor_status(year: int, cfg: Config, data_dir: Path = DATA_DIR) -> tuple[float, str]:
    turnover = _r(sum(r.income for r in year_rows(year, cfg, data_dir)))
    share = turnover / cfg.kor_threshold
    msg = f"KOR: omzet {year} tot nu toe {eur(turnover)} van {eur(cfg.kor_threshold)} ({share:.0%})."
    if turnover > cfg.kor_threshold:
        msg += " GRENS OVERSCHREDEN: direct met Tim en een fiscalist bespreken."
    elif share >= cfg.kor_warn_fraction:
        msg += " Let op: dicht bij de grens."
    return turnover, msg


def report(ledger: Ledger, cfg: Config, today: date | None = None, data_dir: Path = DATA_DIR) -> str:
    s = summarize(ledger, cfg, today)
    _, kor = kor_status(int(ledger.month[:4]), cfg, data_dir)
    lines = [
        f"# Boekhouding {month_label(ledger.month)} – stand {(today or date.today()):%d-%m-%Y}",
        "",
        "| Kerncijfer | Waarde |", "|---|---|",
        f"| Gefactureerd deze maand | {eur(s.income)} |",
        f"| Ontvangen deze maand | {eur(s.received)} |",
        f"| Uitgaven | {eur(s.expenses)} |",
        f"| Netto resultaat | {eur(s.net)} |",
        f"| Gegeven sessies | {s.sessions_given} (geannuleerd: {s.sessions_cancelled}) |",
        f"| Facturabele uren | {s.billable_hours:.2f} |",
        f"| Fietskilometers (memo) | {s.travel_km:.1f} km = {eur(s.travel_allowance)} |",
        f"| Openstaande facturen | {eur(sum(i.amount for i in s.open_invoices_end))} |",
        f"| Onderhanden werk (nog niet gefactureerd) | {eur(sum(w.amount for w in s.wip_end))} "
        f"({len(s.wip_end)} sessies) |",
        "", kor, "", "## Controles",
    ]
    lines += [f"- {'OK' if ok else 'CONTROLEER'}: {name} ({detail})" for name, ok, detail in s.checks] or ["- Geen controles van toepassing."]
    lines += ["", "## Aandachtspunten"]
    lines += [f"- {a}" for a in s.attention + ledger.notes] or ["- Geen."]
    return "\n".join(lines) + "\n"


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tools.bookkeeping")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").add_argument("month")
    a = sub.add_parser("add")
    a.add_argument("month")
    a.add_argument("kind", choices=list(EntryKind.__args__))
    a.add_argument("data", help="JSON object (or plain text for a note)")
    r = sub.add_parser("report")
    r.add_argument("month")
    r.add_argument("--today", type=date.fromisoformat)
    r.add_argument("--out", type=Path)
    b = sub.add_parser("build")
    b.add_argument("month")
    args = p.parse_args(argv)

    try:
        if args.cmd == "init":
            print(f"created {ledger_path(args.month)}: {init_month(args.month, load_config()).opening.model_dump_json()}")
        elif args.cmd == "add":
            cfg = load_config()
            ledger = load_ledger(args.month)
            data = args.data if args.kind == "note" else json.loads(args.data)
            save_ledger(add_entry(ledger, args.kind, data, cfg))
            print(f"added {args.kind} to {args.month}")
        elif args.cmd == "report":
            text = report(load_ledger(args.month), load_config(), args.today)
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(text)
            print(text)
        elif args.cmd == "build":
            # under `python -m` this module is __main__; use the importable copy so
            # the Pydantic classes match the ones bookkeeping_xlsx works with
            from tools import bookkeeping as bk
            from tools.bookkeeping_xlsx import build_month, build_year
            cfg = bk.load_config()
            print(build_month(bk.load_ledger(args.month), cfg))
            print(build_year(int(args.month[:4]), cfg))
    except (InvalidEntry, ValueError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
