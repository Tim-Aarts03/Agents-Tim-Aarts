import json
from datetime import date

import pytest
from openpyxl import Workbook, load_workbook

from tools.bookkeeping import (Config, InvalidEntry, Ledger, add_entry, init_month, kor_status, load_ledger,
                               rate_on, report, save_ledger, summarize)
from tools.bookkeeping_xlsx import NotOurs, build_month, build_year

TODAY = date(2026, 11, 19)


@pytest.fixture
def cfg():
    return Config.model_validate({
        "owner": "Test Owner", "business": "Test Vitality", "client": "Test Client", "location": "Test Park",
        "rates": [{"valid_from": "2026-01-01", "amount": 80}, {"valid_from": "2026-09-29", "amount": 100}],
        "session_time": "16:15–17:00", "session_hours": 0.75, "travel_hours_one_way": 0.15,
        "ride": {"vehicle": "Bike", "origin": "Home 1", "destination": "Park 2", "km_round_trip": 7.6,
                 "rate_per_km": 0.23},
    })


@pytest.fixture
def nov(cfg):
    led = Ledger(month="2026-11")
    add_entry(led, "opening_invoice", {"number": "001", "date": "2026-10-07", "client": "Test Client",
                                       "description": "11 sessies", "amount": 880}, cfg)
    add_entry(led, "opening_wip", {"date": "2026-10-27", "client": "Test Client", "amount": 100}, cfg)
    return led


def test_rate_changes_on_valid_from(cfg):
    assert rate_on(date(2026, 9, 22), cfg) == 80
    assert rate_on(date(2026, 9, 29), cfg) == 100


def test_summary_of_sessions_and_expenses(cfg, nov):
    add_entry(nov, "session", {"date": "2026-11-03", "participants": 8}, cfg)
    add_entry(nov, "session", {"date": "2026-11-10", "participants": 0}, cfg)  # cancelled
    add_entry(nov, "expense", {"date": "2026-11-03", "description": "Eiwitsnack", "shop": "AH",
                               "amount": 4.53, "bank_amount": 4.53}, cfg)
    s = summarize(nov, cfg, TODAY)
    assert (s.sessions_given, s.sessions_cancelled) == (1, 1)
    assert s.billable_hours == 0.75 and s.travel_km == 7.6 and s.travel_allowance == 1.75
    assert s.expenses == 4.53 and s.net == -4.53
    assert [w.date for w in s.wip_end] == [date(2026, 10, 27), date(2026, 11, 3)]
    assert all(ok for _, ok, _ in s.checks)


def test_overdue_invoice_flagged(cfg, nov):
    s = summarize(nov, cfg, TODAY)
    assert any("001" in a and "21-10-2026" in a for a in s.attention)


def test_payment_closes_invoice(cfg, nov):
    add_entry(nov, "payment", {"invoice": "001", "date": "2026-11-12", "amount": 880}, cfg)
    s = summarize(nov, cfg, TODAY)
    assert s.open_invoices_end == [] and s.received == 880 and s.income == 0
    assert not any("001" in a for a in s.attention)


def test_invoice_settles_wip_and_checks_amount(cfg, nov):
    add_entry(nov, "session", {"date": "2026-11-03", "participants": 5}, cfg)
    add_entry(nov, "invoice", {"number": "002", "date": "2026-11-04", "client": "Test Client",
                               "description": "2 sessies", "amount": 150,
                               "sessions": ["2026-10-27", "2026-11-03"]}, cfg)
    s = summarize(nov, cfg, TODAY)
    assert s.wip_end == [] and s.income == 150
    check = next(c for c in s.checks if c[0].startswith("Factuur 002"))
    assert check[1] is False and "€ 200,00" in check[2]


def test_bank_difference_is_flagged(cfg, nov):
    add_entry(nov, "expense", {"date": "2026-11-03", "description": "x", "shop": "AH", "amount": 5,
                               "bank_amount": 4.5}, cfg)
    assert summarize(nov, cfg, TODAY).checks[0][1] is False


def test_unconfirmed_pin_needs_bank_but_cash_does_not(cfg, nov):
    add_entry(nov, "expense", {"date": "2026-11-03", "description": "x", "shop": "AH", "amount": 5}, cfg)
    add_entry(nov, "expense", {"date": "2026-11-04", "description": "y", "shop": "Jumbo", "amount": 3,
                               "payment_method": "Contant"}, cfg)
    att = summarize(nov, cfg, TODAY).attention
    assert any("AH" in a for a in att) and not any("Jumbo" in a for a in att)


@pytest.mark.parametrize("kind,data,msg", [
    ("expense", {"date": "2026-10-31", "description": "x", "shop": "AH", "amount": 5}, "not in"),
    ("expense", {"date": "2026-11-03", "description": "x", "shop": "AH", "amount": -5}, "greater than"),
    ("payment", {"invoice": "999", "date": "2026-11-03", "amount": 5}, "unknown invoice"),
    ("session", {"date": "2025-01-01", "participants": 3}, "not in"),
])
def test_invalid_entries_refused(cfg, nov, kind, data, msg):
    with pytest.raises((InvalidEntry, ValueError), match=msg):
        add_entry(nov, kind, data, cfg)


def test_duplicates_refused(cfg, nov):
    e = {"date": "2026-11-03", "description": "x", "shop": "AH", "amount": 5}
    add_entry(nov, "expense", e, cfg)
    with pytest.raises(InvalidEntry, match="duplicate"):
        add_entry(nov, "expense", e, cfg)
    add_entry(nov, "session", {"date": "2026-11-03", "participants": 3}, cfg)
    with pytest.raises(InvalidEntry, match="already"):
        add_entry(nov, "session", {"date": "2026-11-03", "participants": 4}, cfg)


def test_init_carries_closing_items_over(cfg, nov, tmp_path):
    add_entry(nov, "session", {"date": "2026-11-03", "participants": 5}, cfg)
    save_ledger(nov, tmp_path)
    dec = init_month("2026-12", cfg, tmp_path)
    assert [i.number for i in dec.opening.open_invoices] == ["001"]
    assert len(dec.opening.wip) == 2 and load_ledger("2026-12", tmp_path) == dec
    with pytest.raises(InvalidEntry):
        init_month("2026-12", cfg, tmp_path)


def test_kor_uses_history_and_ledgers(cfg, nov, tmp_path):
    (tmp_path / "history_2026.json").write_text(json.dumps([{
        "month": "2026-09", "file": "x.xlsx", "income": 15000, "expenses": 0, "sessions": 0,
        "billable_hours": 0, "travel_allowance": 0, "open_invoices_end": 0, "wip_end": 0, "status": "x"}]))
    add_entry(nov, "invoice", {"number": "002", "date": "2026-11-04", "client": "c", "description": "d",
                               "amount": 1000}, cfg)
    save_ledger(nov, tmp_path)
    turnover, msg = kor_status(2026, cfg, tmp_path)
    assert turnover == 16000 and "dicht bij de grens" in msg


def test_report_is_dutch_markdown(cfg, nov, tmp_path):
    text = report(nov, cfg, TODAY, tmp_path)
    assert text.startswith("# Boekhouding November 2026") and "Aandachtspunten" in text


def test_build_month_and_year(cfg, nov, tmp_path):
    add_entry(nov, "session", {"date": "2026-11-03", "participants": 5}, cfg)
    add_entry(nov, "expense", {"date": "2026-11-03", "description": "x", "shop": "AH", "amount": 5}, cfg)
    save_ledger(nov, tmp_path)
    path = build_month(nov, cfg, tmp_path, TODAY, data_dir=tmp_path)
    wb = load_workbook(path)
    assert wb.sheetnames == ["Overzicht", "Inkomsten en uitgaven", "Reiskosten", "Urenregistratie",
                             "Sessies", "Bonnen", "Overdracht"]
    assert wb["Inkomsten en uitgaven"]["G4"].value == 5
    assert wb["Overzicht"]["C7"].value.startswith("='Inkomsten en uitgaven'!G")
    build_month(nov, cfg, tmp_path, TODAY, data_dir=tmp_path)  # own file may be rebuilt
    year = load_workbook(build_year(2026, cfg, tmp_path, tmp_path)).active
    assert year["B15"].value == "November" and year["D15"].value == 0 and year["G15"].value == 1


def test_never_overwrites_hand_made_files(cfg, nov, tmp_path):
    manual = Workbook()
    manual.save(tmp_path / "Administratie_Test_Owner_2026-11.xlsx")
    with pytest.raises(NotOurs):
        build_month(nov, cfg, tmp_path, TODAY, data_dir=tmp_path)
    manual.save(tmp_path / "Jaaroverzicht_Test_Owner_2026.xlsx")
    build_year(2026, cfg, tmp_path, tmp_path)
    assert (tmp_path / "Jaaroverzicht_Test_Owner_2026_origineel.xlsx").exists()


def test_cli_build_runs_as_module(cfg, nov, tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    repo = Path(__file__).resolve().parents[1]
    (tmp_path / "knowledge").mkdir()
    (tmp_path / "knowledge" / "private_bookkeeping.json").write_text(cfg.model_dump_json())
    save_ledger(nov, tmp_path / "Boekhouding" / "data")
    run = subprocess.run([sys.executable, "-m", "tools.bookkeeping", "build", "2026-11"], cwd=tmp_path,
                         env={"PYTHONPATH": str(repo)}, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert (tmp_path / "Boekhouding" / "Maandelijkse administratie" / "Administratie_Test_Owner_2026-11.xlsx").exists()


def test_session_without_participant_count_counts_as_given(cfg, nov):
    add_entry(nov, "session", {"date": "2026-11-03"}, cfg)
    assert summarize(nov, cfg, TODAY).sessions_given == 1


def test_follow_up_replaces_reminder_suggestion(cfg, nov):
    nov.opening.open_invoices[0].follow_up = "Tim regelt de betaling zelf."
    att = summarize(nov, cfg, TODAY).attention
    assert any("regelt" in a for a in att) and not any("herinnering" in a for a in att)


def test_layout_follows_tims_sheet(cfg, nov, tmp_path):
    add_entry(nov, "session", {"date": "2026-11-03", "participants": 3, "rating": 8}, cfg)
    add_entry(nov, "expense", {"date": "2026-11-04", "description": "Yoga matten – Marktplaats", "shop": "Marktplaats",
                               "amount": 50, "payment_method": "Contant", "status": "Betaald (geen bon)"}, cfg)
    wb = load_workbook(build_month(nov, cfg, tmp_path, TODAY, data_dir=tmp_path))
    ie, uren, sess = wb["Inkomsten en uitgaven"], wb["Urenregistratie"], wb["Sessies"]
    assert [ie["B1"].value, ie["C1"].value, ie["D1"].value] == ["Test Owner", 2026, "November"]
    assert ie["D4"].value == "Yoga matten – Marktplaats" and ie["K4"].value == "Betaald (geen bon)"
    assert (uren["F4"].value, uren["G4"].value, uren["I4"].value) == (16.1, 16.25, "=G4-F4-H4")
    assert uren["F5"].value == 16.25 and uren["G5"].value == 17
    assert sess["E3"].value == "Cijfer" and sess["E4"].value == 8
    assert "(voorlopig)" in wb["Overzicht"]["B1"].value
    assert wb["Inkomsten en uitgaven"]["F6"].value == "=SUM(F4:F5)"  # spare row inside the range
