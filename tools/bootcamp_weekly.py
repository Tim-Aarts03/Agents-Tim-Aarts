"""Deterministic steps of the automatic Wednesday promotion run.

The scheduled task calls `check` first (stop early if anything is missing),
then `compose` with the pitch from mail-promo-writer. The draft itself is saved
by tools.mail_sender after qa-fact-checker passes.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from pydantic import BaseModel

from tools.bootcamp_mail import MAIL_LOG, RECIPIENTS_FILE, Group, Pitch, load_recipients, next_tuesday, promo_mail, read_mail_log
from tools.mail_sender import mail_hash

FORM_FILE = Path("knowledge/bootcamp_form.json")
OUTPUT_DIR = Path("output/mail")
GROUP = Group.HOF_VAN_JACOB
FIXED = "fixed"  # one reusable form instead of a new one per week


class FormLink(BaseModel):
    link: str
    session: str  # ISO date of the Tuesday this form is for, or "fixed"


class NotReady(Exception):
    pass


def check(send_date: date, form_file: Path = FORM_FILE, log_path: Path = MAIL_LOG,
          recipients_file: Path = RECIPIENTS_FILE) -> str:
    """Return the form link, or raise NotReady with a reason Tim can act on."""
    session = next_tuesday(send_date).isoformat()
    done = [r for r in read_mail_log(log_path)
            if r["group"] == GROUP.value and r["session_date"] == session and r["kind"] in ("promo_sent", "promo_draft")]
    if done:
        raise NotReady(f"promotion mail for {session} already {done[-1]['kind'].removeprefix('promo_')}")
    if not recipients_file.exists() or not load_recipients(recipients_file).get(GROUP):
        raise NotReady("no recipient in knowledge/private_mail_recipients.json")
    if not form_file.exists():
        raise NotReady("no sign-up link in knowledge/bootcamp_form.json")
    form = FormLink.model_validate_json(form_file.read_text(encoding="utf-8"))
    if form.session not in (FIXED, session):
        raise NotReady(f"sign-up link is for {form.session}, not for {session}; Tim must send the new link")
    return form.link


def compose(send_date: date, pitch: str, **kwargs: Path) -> tuple[Path, str]:
    link = check(send_date, **kwargs)
    recipients = load_recipients(kwargs.get("recipients_file", RECIPIENTS_FILE))[GROUP]
    mail = promo_mail(GROUP, Pitch(text=pitch), link, send_date, recipients)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"promo_{GROUP.value}_{send_date.isoformat()}.json"
    path.write_text(mail.model_dump_json(indent=2), encoding="utf-8")
    return path, mail_hash(mail)


def main() -> None:
    """CLI:
    python -m tools.bootcamp_weekly check [--date YYYY-MM-DD]
    python -m tools.bootcamp_weekly compose --pitch "..." [--date YYYY-MM-DD]
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["check", "compose"])
    parser.add_argument("--pitch", default="")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    try:
        if args.action == "check":
            print(json.dumps({"ready": True, "link": check(args.date), "session": next_tuesday(args.date).isoformat()}))
        else:
            path, h = compose(args.date, args.pitch)
            print(json.dumps({"ready": True, "draft": str(path), "hash": h}))
    except NotReady as e:
        print(json.dumps({"ready": False, "reason": str(e)}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
