import json
from datetime import date

import pytest

from tools import bootcamp_weekly
from tools.bootcamp_mail import log_mail
from tools.bootcamp_weekly import NotReady, check, compose

WED = date(2026, 11, 25)  # session Tuesday 1 December


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr(bootcamp_weekly, "OUTPUT_DIR", tmp_path / "out")
    recipients = tmp_path / "r.json"
    recipients.write_text(json.dumps({"hof_van_jacob": ["contact@example.org"]}))
    form = tmp_path / "form.json"
    log = tmp_path / "log.csv"

    def kw(session="2026-12-01"):
        form.write_text(json.dumps({"link": "https://forms.gle/x", "session": session}))
        return {"form_file": form, "log_path": log, "recipients_file": recipients}

    return kw, log


def test_ready_with_link_for_this_session(files):
    kw, _ = files
    assert check(WED, **kw()) == "https://forms.gle/x"


def test_fixed_form_is_always_valid(files):
    kw, _ = files
    assert check(WED, **kw("fixed")) == "https://forms.gle/x"


def test_old_link_stops_run(files):
    kw, _ = files
    with pytest.raises(NotReady, match="new link"):
        check(WED, **kw("2026-11-24"))


@pytest.mark.parametrize("kind", ["promo_sent", "promo_draft"])
def test_no_second_mail_for_same_session(files, kind):
    kw, log = files
    log_mail(WED, kind, "hof_van_jacob", "x", path=log)
    with pytest.raises(NotReady, match="already"):
        check(WED, **kw())


def test_compose_writes_draft_with_hash(files):
    kw, _ = files
    path, h = compose(WED, "Meld je aan en kom lekker bewegen. Neem een collega mee!", **kw())
    data = json.loads(path.read_text())
    assert data["to"] == ["contact@example.org"]
    assert "1 december" in data["subject"] and len(h) == 12
