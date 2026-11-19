"""Sales invoices for T.A Vitality: numbering, amounts, due date, PDF and booking.

All arithmetic lives here; the LLM agent only picks the sessions and the date.
Flow: `draft` writes a concept (Markdown for the fact check + PDF) to
`output/finance/`; after Tim approves, `finalize` copies the PDF to
`Boekhouding/01 Verkoop Facturen/` and books the invoice in the ledger.

Usage:
    python -m tools.invoice next-number
    python -m tools.invoice unbilled 2026-12
    python -m tools.invoice draft --date 2026-12-16 [--sessions 2026-09-29,2026-10-06] [--today 2026-12-16]
    python -m tools.invoice finalize 002 --approved
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

from pydantic import BaseModel

from tools import bookkeeping as bk

SALES_DIR = bk.BOOK_DIR / "01 Verkoop Facturen"
DRAFT_DIR = Path("output/finance")
NUMBER_IN_FILE = re.compile(r"_(\d{3,})_")


class InvoiceProfile(BaseModel):
    """Fixed invoice details; lives in knowledge/private_bookkeeping.json under "invoice"."""
    sender_lines: list[str]
    kvk: str
    vat_id: str
    iban: str
    account_name: str
    client_name: str
    client_lines: list[str]
    description: str
    file_prefix: str = "Factuur"
    file_owner: str = "Tim_Aarts"


class Line(BaseModel):
    description: str
    quantity: int
    rate: float
    total: float
    dates: list[date]


class Draft(BaseModel):
    number: str
    date: date
    due_date: date
    client: str  # full name as in the ledger
    lines: list[Line]
    total: float
    sessions: list[date]
    warnings: list[str] = []

    def booking(self) -> dict:
        """Invoice entry for tools.bookkeeping, in the ledger's description style."""
        s = sorted(self.sessions)
        rates = " + ".join(f"{ln.quantity} × {bk.eur(ln.rate)}" for ln in self.lines)
        return {
            "number": self.number, "date": self.date.isoformat(), "client": self.client,
            "description": f"{len(s)} bootcamplessen ({rates}; {s[0]:%d-%m} t/m {s[-1]:%d-%m})",
            "amount": self.total, "sessions": [d.isoformat() for d in s],
            "due_date": self.due_date.isoformat(),
        }


def load_profile(path: Path = bk.CONFIG_FILE) -> InvoiceProfile:
    data = json.loads(path.read_text())
    if "invoice" not in data:
        raise bk.InvalidEntry(f'no "invoice" details in {path}')
    return InvoiceProfile.model_validate(data["invoice"])


def long_date(d: date) -> str:
    return f"{d.day} {bk.MONTHS_NL[d.month - 1]} {d.year}"


# ---------- numbering ----------

def used_numbers(data_dir: Path = bk.DATA_DIR, sales_dir: Path = SALES_DIR) -> set[int]:
    """Every invoice number seen in any ledger or as a PDF in the sales folder."""
    nums: set[int] = set()
    for path in data_dir.glob("????-??.json"):
        led = bk.Ledger.model_validate_json(path.read_text())
        nums |= {int(i.number) for i in led.invoices + led.opening.open_invoices if i.number.isdigit()}
    if sales_dir.is_dir():
        for f in sales_dir.iterdir():
            if m := NUMBER_IN_FILE.search(f.name):
                nums.add(int(m.group(1)))
    return nums


def next_number(data_dir: Path = bk.DATA_DIR, sales_dir: Path = SALES_DIR) -> str:
    return f"{max(used_numbers(data_dir, sales_dir), default=0) + 1:03d}"


# ---------- drafting ----------

def unbilled(month: str, cfg: bk.Config, data_dir: Path = bk.DATA_DIR) -> list[bk.WipItem]:
    path = bk.ledger_path(month, data_dir)
    if not path.exists():
        raise bk.InvalidEntry(f"no ledger for {month}; run `python -m tools.bookkeeping init {month}` first")
    return bk.summarize(bk.load_ledger(month, data_dir), cfg).wip_end


def make_draft(inv_date: date, cfg: bk.Config, profile: InvoiceProfile, sessions: list[date] | None = None,
               data_dir: Path = bk.DATA_DIR, sales_dir: Path = SALES_DIR, today: date | None = None) -> Draft:
    """Invoice for unbilled sessions; refuses anything already billed or not yet given."""
    today = today or date.today()
    wip = {w.date: w for w in unbilled(bk.month_of(inv_date), cfg, data_dir)}
    chosen = sorted(set(sessions)) if sessions else sorted(wip)
    if not chosen:
        raise bk.InvalidEntry("no unbilled sessions to invoice")
    unknown = [d for d in chosen if d not in wip]
    if unknown:
        raise bk.InvalidEntry("not unbilled (already invoiced or never booked): "
                              + ", ".join(f"{d:%d-%m-%Y}" for d in unknown))
    later = [d for d in chosen if d > inv_date]
    if later:
        raise bk.InvalidEntry("session after the invoice date: " + ", ".join(f"{d:%d-%m-%Y}" for d in later))

    by_rate: dict[float, list[date]] = {}
    for d in chosen:
        by_rate.setdefault(wip[d].amount, []).append(d)
    lines = [Line(description=profile.description, quantity=len(ds), rate=rate,
                  total=bk._r(len(ds) * rate), dates=ds) for rate, ds in sorted(by_rate.items())]

    warnings: list[str] = []
    if inv_date > today:
        warnings.append(f"Factuurdatum {inv_date:%d-%m-%Y} ligt in de toekomst.")
    c = cfg.contract
    if c and any(c.start <= d <= c.end for d in chosen):
        if inv_date <= c.end:
            warnings.append(f"Contract loopt t/m {c.end:%d-%m-%Y}; afgesproken is factureren achteraf.")
        in_contract = [d for d in wip if c.start <= d <= c.end]
        if inv_date > c.end and len(in_contract) != c.sessions:
            warnings.append(f"Contract: {c.sessions} lessen afgesproken, {len(in_contract)} nog te factureren "
                            "in de boekhouding. Klopt het aantal?")

    return Draft(number=next_number(data_dir, sales_dir), date=inv_date,
                 due_date=inv_date + timedelta(days=cfg.payment_term_days), client=cfg.client,
                 lines=lines, total=bk._r(sum(ln.total for ln in lines)), sessions=chosen, warnings=warnings)


def payment_text(d: Draft, p: InvoiceProfile, term_days: int) -> str:
    return (f"Ik verzoek u vriendelijk het factuurbedrag van {bk.eur(d.total)} binnen {term_days} dagen "
            f"(vóór {long_date(d.due_date)}) over te maken naar IBAN {p.iban} ten name van "
            f"{p.account_name}, onder vermelding van factuurnummer {d.number}.")


KOR_NOTE = "* Vrijstelling van btw wegens toepassing van de kleineondernemersregeling (KOR)."


def lesson_dates(ln: Line) -> str:
    return "Lesdata: " + ", ".join(f"{d.day}-{d.month}" for d in ln.dates)


def to_markdown(d: Draft, p: InvoiceProfile, term_days: int) -> str:
    """Full invoice text, for qa-fact-checker and Tim's review."""
    rows = [f"| {ln.description} ({lesson_dates(ln)}) | {ln.quantity} | {bk.eur(ln.rate)} | 0%* | "
            f"{bk.eur(ln.total)} |" for ln in d.lines]
    out = [
        f"# CONCEPT factuur {d.number}", "",
        "**Van:** " + ", ".join(p.sender_lines) + f", KVK: {p.kvk}, BTW-id: {p.vat_id}",
        "**Aan:** " + ", ".join([p.client_name, *p.client_lines]), "",
        f"- Factuurdatum: {long_date(d.date)}",
        f"- Factuurnummer: {d.number}",
        f"- Vervaldatum: {long_date(d.due_date)}", "",
        "| Omschrijving | Aantal | Tarief | BTW | Totaal |", "|---|---|---|---|---|", *rows, "",
        f"Subtotaal: {bk.eur(d.total)}  ", "BTW (0%): € 0,00  ", f"**Totaal te betalen: {bk.eur(d.total)}**", "",
        KOR_NOTE, "", "## Betalingsinstructie", payment_text(d, p, term_days), "",
    ]
    if d.warnings:
        out += ["## Let op (niet op de factuur)", *[f"- {w}" for w in d.warnings], ""]
    return "\n".join(out)


def to_pdf(d: Draft, p: InvoiceProfile, term_days: int, path: Path) -> Path:
    """PDF in the layout of Tim's invoice 001."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    blue, grey_bg, grey = colors.HexColor("#1F4E79"), colors.HexColor("#F2F2F2"), colors.HexColor("#808080")
    base = ParagraphStyle("b", fontName="Helvetica", fontSize=10, leading=13)
    st = {
        "title": ParagraphStyle("t", parent=base, fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=blue),
        "head": ParagraphStyle("h", parent=base, fontName="Helvetica-Bold", textColor=blue),
        "label": ParagraphStyle("l", parent=base, fontName="Helvetica-Bold", fontSize=8, textColor=grey),
        "value": ParagraphStyle("v", parent=base, fontName="Helvetica-Bold", fontSize=11),
        "th": ParagraphStyle("th", parent=base, fontName="Helvetica-Bold", textColor=colors.white),
        "small": ParagraphStyle("s", parent=base, fontSize=8, leading=10, textColor=grey),
        "right": ParagraphStyle("r", parent=base, alignment=TA_RIGHT, textColor=grey),
        "total": ParagraphStyle("tt", parent=base, alignment=TA_RIGHT, fontName="Helvetica-Bold", fontSize=11),
        "note": ParagraphStyle("n", parent=base, fontName="Helvetica-Oblique", fontSize=8),
        "h2": ParagraphStyle("h2", parent=base, fontName="Helvetica-Bold", fontSize=13, textColor=blue),
    }
    P = Paragraph
    width = A4[0] - 40 * mm

    sender = [P("Van:", st["head"]), *[P(x, base) for x in p.sender_lines],
              P(f"KVK: {p.kvk}", base), P(f"BTW-id: {p.vat_id}", base)]
    client = [P("Aan:", st["head"]), P(p.client_name, base), *[P(x, base) for x in p.client_lines]]
    parties = Table([[sender, client]], colWidths=[width / 2] * 2)
    parties.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))

    meta = Table([[P("Factuurdatum", st["label"]), P("Factuurnummer", st["label"]), P("Vervaldatum", st["label"])],
                  [P(long_date(d.date), st["value"]), P(d.number, st["value"]), P(long_date(d.due_date), st["value"])]],
                 colWidths=[width / 3] * 3)
    meta.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), grey_bg)]))

    th_right = ParagraphStyle("thr", parent=st["th"], alignment=TA_RIGHT)
    rows = [[P("Omschrijving", st["th"])] + [P(h, th_right) for h in ("Aantal", "Tarief", "BTW", "Totaal")]]
    for ln in d.lines:
        rows.append([[P(ln.description, base), P(lesson_dates(ln), st["small"])], str(ln.quantity),
                     bk.eur(ln.rate), "0%*", bk.eur(ln.total)])
    items = Table(rows, colWidths=[width * 0.5, width * 0.11, width * 0.14, width * 0.1, width * 0.15])
    items.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), blue), ("BACKGROUND", (0, 1), (-1, -1), grey_bg),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    story = [
        P("FACTUUR", st["title"]), Spacer(1, 4 * mm), parties, Spacer(1, 8 * mm), meta, Spacer(1, 10 * mm),
        items, Spacer(1, 10 * mm),
        P(f"Subtotaal: {bk.eur(d.total)}", st["right"]), P("BTW (0%): € 0,00", st["right"]), Spacer(1, 3 * mm),
        P(f'Totaal te betalen: <font size="14" color="#1F4E79">{bk.eur(d.total)}</font>', st["total"]),
        Spacer(1, 10 * mm), P(KOR_NOTE, st["note"]), Spacer(1, 12 * mm),
        P("Betalingsinstructie", st["h2"]), Spacer(1, 2 * mm), P(payment_text(d, p, term_days), base),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=25 * mm,
                      title=f"Factuur {d.number}", author=p.sender_lines[0]).build(story)
    return path


def pdf_name(d: Draft, p: InvoiceProfile) -> str:
    return f"{p.file_prefix}_{d.number}_{p.file_owner}.pdf"


def write_draft(d: Draft, cfg: bk.Config, p: InvoiceProfile, out_dir: Path = DRAFT_DIR) -> tuple[Path, Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = out_dir / f"invoice_{d.number}.json"
    md = out_dir / f"invoice_{d.number}_{d.date.isoformat()}.md"
    spec.write_text(d.model_dump_json(indent=2) + "\n")
    md.write_text(to_markdown(d, p, cfg.payment_term_days))
    pdf = to_pdf(d, p, cfg.payment_term_days, out_dir / pdf_name(d, p))
    return md, pdf, spec


# ---------- finalizing ----------

def finalize(number: str, cfg: bk.Config, p: InvoiceProfile, out_dir: Path = DRAFT_DIR,
             data_dir: Path = bk.DATA_DIR, sales_dir: Path = SALES_DIR) -> Path:
    """Approved draft → PDF in the sales folder + invoice booked. Never overwrites."""
    spec = out_dir / f"invoice_{number}.json"
    if not spec.exists():
        raise bk.InvalidEntry(f"no draft {spec}; run `draft` first")
    d = Draft.model_validate_json(spec.read_text())
    if int(d.number) in used_numbers(data_dir, sales_dir):
        raise bk.InvalidEntry(f"invoice number {d.number} is already used")
    wip = {w.date for w in unbilled(bk.month_of(d.date), cfg, data_dir)}
    if not set(d.sessions) <= wip:
        raise bk.InvalidEntry("draft is outdated: some sessions are no longer unbilled; make a new draft")
    src = out_dir / pdf_name(d, p)
    dest = sales_dir / pdf_name(d, p)
    if dest.exists():
        raise bk.InvalidEntry(f"{dest} already exists")

    month = bk.month_of(d.date)
    ledger = bk.add_entry(bk.load_ledger(month, data_dir), "invoice", d.booking(), cfg)
    sales_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    bk.save_ledger(ledger, data_dir)
    return dest


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tools.invoice")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("next-number")
    sub.add_parser("unbilled").add_argument("month")
    dr = sub.add_parser("draft")
    dr.add_argument("--date", type=date.fromisoformat, required=True)
    dr.add_argument("--sessions", help="comma-separated YYYY-MM-DD; default: all unbilled")
    dr.add_argument("--today", type=date.fromisoformat)
    fi = sub.add_parser("finalize")
    fi.add_argument("number")
    fi.add_argument("--approved", action="store_true", help="only after Tim approved this exact draft")
    args = ap.parse_args(argv)

    try:
        bk.ensure_book_dir()
        cfg = bk.load_config()
        if args.cmd == "next-number":
            print(next_number())
        elif args.cmd == "unbilled":
            for w in unbilled(args.month, cfg):
                print(f"{w.date.isoformat()}  {bk.eur(w.amount)}")
        elif args.cmd == "draft":
            sessions = [date.fromisoformat(s) for s in args.sessions.split(",")] if args.sessions else None
            p = load_profile()
            d = make_draft(args.date, cfg, p, sessions, today=args.today)
            for path in write_draft(d, cfg, p):
                print(path)
            print(f"invoice {d.number}: {len(d.sessions)} sessions, total {bk.eur(d.total)}, due {d.due_date}")
            for w in d.warnings:
                print(f"WARNING: {w}")
        elif args.cmd == "finalize":
            if not args.approved:
                raise bk.InvalidEntry("finalize needs --approved (only after Tim approved the draft)")
            print(f"saved {finalize(args.number, cfg, load_profile())} and booked the invoice")
    except (bk.InvalidEntry, ValueError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
