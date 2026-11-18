import json
from datetime import date
from unittest.mock import patch

import pytest

from tools.bootcamp_mail import Group, Mail, read_mail_log
from tools import mail_sender
from tools.mail_sender import SendRefused, mail_hash, send

SEND_DATE = date(2026, 11, 18)
ALLOWED = "contact@example.org"


@pytest.fixture
def setup(tmp_path):
    recipients = tmp_path / "recipients.json"
    recipients.write_text(json.dumps({"hof_van_jacob": [ALLOWED], "jacob_kliniek": []}))
    log = tmp_path / "log.csv"

    def make_draft(to=(ALLOWED,), subject="Beweegsessie dinsdag 24 november – meld je aan"):
        mail = Mail(to=list(to), subject=subject, body="Beste collega's,\n\nPitch hier.\n\nTot dinsdag!")
        draft = tmp_path / "draft.json"
        draft.write_text(mail.model_dump_json())
        return draft, mail_hash(mail)

    return recipients, log, make_draft


def run(draft, hash_, recipients, log):
    return send(draft, Group.HOF_VAN_JACOB, hash_, SEND_DATE, recipients_file=recipients, log_path=log)


def test_sends_approved_mail_and_logs(setup):
    recipients, log, make_draft = setup
    draft, h = make_draft()
    with patch.object(mail_sender.subprocess, "run") as osascript:
        run(draft, h, recipients, log)
    args = osascript.call_args.args[0]
    assert args[0] == "osascript" and args[-1] == ALLOWED
    rows = read_mail_log(log)
    assert rows[0]["kind"] == "promo_sent" and rows[0]["session_date"] == "2026-11-24"
    assert rows[0]["pitch"] == "Pitch hier."


def test_refuses_changed_draft(setup):
    recipients, log, make_draft = setup
    draft, _ = make_draft()
    with patch.object(mail_sender.subprocess, "run") as osascript, pytest.raises(SendRefused, match="hash"):
        run(draft, "000000000000", recipients, log)
    osascript.assert_not_called()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"to": ("stranger@example.org",)},
        {"to": (ALLOWED, "stranger@example.org")},
        {"to": ()},
        {"subject": "Iets anders"},
    ],
)
def test_refuses_unapproved_recipients_or_subject(setup, kwargs):
    recipients, log, make_draft = setup
    draft, h = make_draft(**kwargs)
    with patch.object(mail_sender.subprocess, "run") as osascript, pytest.raises(SendRefused):
        run(draft, h, recipients, log)
    osascript.assert_not_called()


def test_refuses_second_send_for_same_session(setup):
    recipients, log, make_draft = setup
    draft, h = make_draft()
    with patch.object(mail_sender.subprocess, "run") as osascript:
        run(draft, h, recipients, log)
        with pytest.raises(SendRefused, match="already sent"):
            run(draft, h, recipients, log)
    assert osascript.call_count == 1


def test_draft_saves_without_sending_and_does_not_block_send(setup):
    recipients, log, make_draft = setup
    draft, h = make_draft()
    with patch.object(mail_sender.subprocess, "run") as osascript:
        send(draft, Group.HOF_VAN_JACOB, h, SEND_DATE, recipients_file=recipients, log_path=log, draft_only=True)
        script = osascript.call_args.args[0][2]
        assert "save msg" in script and "send msg" not in script
        run(draft, h, recipients, log)
    assert [r["kind"] for r in read_mail_log(log)] == ["promo_draft", "promo_sent"]


@pytest.mark.parametrize("script", [mail_sender.APPLESCRIPT, mail_sender.DRAFT_APPLESCRIPT])
def test_applescript_only_creates_and_sends(script):
    for forbidden in ("mailbox", "every message", "delete", "move", "read status", "do shell script"):
        assert forbidden not in script
