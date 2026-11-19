from datetime import date

import pytest

from tools import bookkeeping as bk
from tools.invoice import (InvoiceProfile, finalize, make_draft, next_number, to_markdown, used_numbers,
                           write_draft)

TODAY = date(2026, 12, 16)


@pytest.fixture
def cfg():
    return bk.Config.model_validate({
        "owner": "Test Owner", "business": "Test Vitality", "client": "Test Client Foundation",
        "location": "Test Park",
        "rates": [{"valid_from": "2026-01-01", "amount": 80}, {"valid_from": "2026-09-29", "amount": 100}],
        "session_time": "16:15–17:00", "session_hours": 0.75, "travel_hours_one_way": 0.15,
        "ride": {"vehicle": "Bike", "origin": "Home 1", "destination": "Park 2", "km_round_trip": 7.6,
                 "rate_per_km": 0.23},
        "payment_term_days": 14,
        "contract": {"start": "2026-09-29", "end": "2026-12-15", "sessions": 3, "rate": 100},
    })


@pytest.fixture
def profile():
    return InvoiceProfile(sender_lines=["Test Vitality", "Street 1"], kvk="00000000", vat_id="NL000000000B00",
                          iban="NL00 TEST 0000 0000 00", account_name="Test Owner", client_name="Test Client",
                          client_lines=["Road 2", "1234 AB Town"], description="Bootcamp lessen",
                          file_owner="Test_Owner")


@pytest.fixture
def dirs(tmp_path, cfg):
    data, sales, out = tmp_path / "data", tmp_path / "sales", tmp_path / "out"
    sales.mkdir()
    (sales / "Factuur_001_Test_Owner.pdf").write_bytes(b"%PDF old")
    led = bk.Ledger(month="2026-12")
    bk.add_entry(led, "opening_invoice", {"number": "001", "date": "2026-09-16", "client": "Test Client Foundation",
                                          "description": "old", "amount": 880}, cfg)
    bk.add_entry(led, "opening_wip", {"date": "2026-09-22", "client": "x", "amount": 80}, cfg)
    bk.add_entry(led, "opening_wip", {"date": "2026-11-17", "client": "x", "amount": 100}, cfg)
    bk.add_entry(led, "session", {"date": "2026-12-08"}, cfg)
    bk.add_entry(led, "session", {"date": "2026-12-15"}, cfg)
    bk.save_ledger(led, data)
    return {"data_dir": data, "sales_dir": sales, "out": out}


def draft(cfg, profile, dirs, inv_date=TODAY, sessions=None):
    return make_draft(inv_date, cfg, profile, sessions, dirs["data_dir"], dirs["sales_dir"], today=TODAY)


def test_next_number_after_ledger_and_pdfs(dirs):
    assert used_numbers(dirs["data_dir"], dirs["sales_dir"]) == {1}
    (dirs["sales_dir"] / "Factuur_007_Test_Owner.pdf").write_bytes(b"x")
    assert next_number(dirs["data_dir"], dirs["sales_dir"]) == "008"


def test_draft_groups_sessions_by_rate(cfg, profile, dirs):
    d = draft(cfg, profile, dirs)
    assert d.number == "002"
    assert [(ln.quantity, ln.rate, ln.total) for ln in d.lines] == [(1, 80, 80), (3, 100, 300)]
    assert d.total == 380
    assert d.due_date == date(2026, 12, 30)
    assert d.client == "Test Client Foundation"


def test_draft_selected_sessions_only(cfg, profile, dirs):
    d = draft(cfg, profile, dirs, sessions=[date(2026, 12, 8), date(2026, 12, 15)])
    assert d.total == 200 and d.sessions == [date(2026, 12, 8), date(2026, 12, 15)]


def test_refuses_unknown_or_billed_session(cfg, profile, dirs):
    with pytest.raises(bk.InvalidEntry, match="not unbilled"):
        draft(cfg, profile, dirs, sessions=[date(2026, 12, 1)])


def test_refuses_session_after_invoice_date(cfg, profile, dirs):
    with pytest.raises(bk.InvalidEntry, match="after the invoice date"):
        draft(cfg, profile, dirs, inv_date=date(2026, 12, 10))


def test_refuses_month_without_ledger(cfg, profile, dirs):
    with pytest.raises(bk.InvalidEntry, match="no ledger"):
        draft(cfg, profile, dirs, inv_date=date(2027, 1, 5))


def test_warns_before_contract_end_and_on_count(cfg, profile, dirs):
    early = draft(cfg, profile, dirs, inv_date=date(2026, 12, 15))
    assert any("achteraf" in w for w in early.warnings)
    assert not any("achteraf" in w for w in draft(cfg, profile, dirs).warnings)
    cfg.contract.sessions = 12
    assert any("12 lessen" in w for w in draft(cfg, profile, dirs).warnings)


def test_markdown_has_all_invoice_facts(cfg, profile, dirs):
    d = draft(cfg, profile, dirs)
    md = to_markdown(d, profile, cfg.payment_term_days)
    for text in ["Factuurnummer: 002", "16 december 2026", "30 december 2026", "€ 380,00", "KVK: 00000000",
                 "NL00 TEST 0000 0000 00", "kleineondernemersregeling", "binnen 14 dagen", "factuurbedrag",
                 "Lesdata: 22-9", "0%*"]:
        assert text in md, text


def test_finalize_saves_pdf_and_books(cfg, profile, dirs):
    d = draft(cfg, profile, dirs)
    md, pdf, _ = write_draft(d, cfg, profile, dirs["out"])
    assert pdf.read_bytes().startswith(b"%PDF") and md.exists()
    dest = finalize("002", cfg, profile, dirs["out"], dirs["data_dir"], dirs["sales_dir"])
    assert dest.name == "Factuur_002_Test_Owner.pdf" and dest.exists()
    led = bk.load_ledger("2026-12", dirs["data_dir"])
    inv = led.invoices[0]
    assert (inv.number, inv.amount, inv.due_date) == ("002", 380, date(2026, 12, 30))
    s = bk.summarize(led, cfg, TODAY)
    assert s.wip_end == [] and all(ok for _, ok, _ in s.checks)
    # a second finalize must not book or overwrite again
    with pytest.raises(bk.InvalidEntry, match="already used"):
        finalize("002", cfg, profile, dirs["out"], dirs["data_dir"], dirs["sales_dir"])
    assert next_number(dirs["data_dir"], dirs["sales_dir"]) == "003"


def test_finalize_refuses_outdated_draft(cfg, profile, dirs):
    d = draft(cfg, profile, dirs)
    write_draft(d, cfg, profile, dirs["out"])
    led = bk.load_ledger("2026-12", dirs["data_dir"])
    bk.add_entry(led, "invoice", {"number": "050", "date": "2026-12-16", "client": "x", "description": "x",
                                  "amount": 100, "sessions": ["2026-12-15"]}, cfg)
    bk.save_ledger(led, dirs["data_dir"])
    with pytest.raises(bk.InvalidEntry, match="outdated"):
        finalize("002", cfg, profile, dirs["out"], dirs["data_dir"], dirs["sales_dir"])


def test_finalize_needs_draft(cfg, profile, dirs):
    with pytest.raises(bk.InvalidEntry, match="no draft"):
        finalize("009", cfg, profile, dirs["out"], dirs["data_dir"], dirs["sales_dir"])
