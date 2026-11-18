"""Send ONE approved weekly bootcamp promotion mail through Apple Mail.

Strict by design (Tim, 2026-11-18): this tool can only send. It never reads,
searches, moves or deletes mail. It refuses unless
- every recipient is in the private recipients file,
- the subject is a weekly bootcamp promotion subject,
- the mail is exactly the one Tim approved (content hash from `preview`),
- this group has not already received a promotion mail for that session.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import date
from pathlib import Path

from tools.bootcamp_mail import MAIL_LOG, RECIPIENTS_FILE, Group, Mail, load_recipients, log_mail, next_tuesday, read_mail_log

SUBJECT_PATTERN = re.compile(r"^Beweegsessie dinsdag \d{1,2} [a-z]+ – meld je aan$")

# Recipients, subject and body are passed as argv so mail text can never be run as AppleScript.
# Only "make new outgoing message" and "send" are used: no access to any mailbox.
APPLESCRIPT = """
on run argv
    set theSubject to item 1 of argv
    set theBody to item 2 of argv
    tell application "Mail"
        set msg to make new outgoing message with properties {subject:theSubject, content:theBody, visible:false}
        tell msg
            repeat with i from 3 to count of argv
                make new to recipient at end of to recipients with properties {address:(item i of argv)}
            end repeat
        end tell
        send msg
    end tell
end run
"""


class SendRefused(Exception):
    pass


def mail_hash(mail: Mail) -> str:
    payload = json.dumps(mail.model_dump(), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def check_mail(mail: Mail, group: Group, send_date: date, allowed: dict[Group, list[str]], log: list[dict[str, str]]) -> None:
    if not mail.to:
        raise SendRefused("no recipients")
    not_allowed = [a for a in mail.to if a not in allowed.get(group, [])]
    if not_allowed:
        raise SendRefused(f"recipients not in the allowed list for {group.value}: {not_allowed}")
    if not SUBJECT_PATTERN.match(mail.subject):
        raise SendRefused(f"subject is not a weekly promotion subject: {mail.subject!r}")
    session = next_tuesday(send_date).isoformat()
    already = [r for r in log if r["kind"] == "promo_sent" and r["group"] == group.value and r["session_date"] == session]
    if already:
        raise SendRefused(f"a promotion mail for {session} was already sent to {group.value}")


def send_via_apple_mail(mail: Mail) -> None:
    subprocess.run(
        ["osascript", "-e", APPLESCRIPT, mail.subject, mail.body, *mail.to],
        check=True, capture_output=True, text=True, timeout=60,
    )


def send(
    draft: Path, group: Group, approved_hash: str, send_date: date,
    recipients_file: Path = RECIPIENTS_FILE, log_path: Path = MAIL_LOG,
) -> Mail:
    mail = Mail.model_validate_json(draft.read_text(encoding="utf-8"))
    if mail_hash(mail) != approved_hash:
        raise SendRefused("draft changed after Tim's approval (hash mismatch); show a new preview")
    check_mail(mail, group, send_date, load_recipients(recipients_file), read_mail_log(log_path))
    send_via_apple_mail(mail)
    log_mail(send_date, "promo_sent", group.value, _pitch_of(mail), path=log_path)
    return mail


def _pitch_of(mail: Mail) -> str:
    parts = mail.body.split("\n\n")
    return parts[1] if len(parts) > 1 else ""


def main() -> None:
    """CLI:
    python -m tools.mail_sender preview --draft output/mail/X.json --group hof_van_jacob
    python -m tools.mail_sender send --draft output/mail/X.json --group hof_van_jacob --approved-hash HASH
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preview", "send"])
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--group", required=True, choices=[g.value for g in Group])
    parser.add_argument("--approved-hash", default="")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    group = Group(args.group)

    if args.action == "preview":
        mail = Mail.model_validate_json(args.draft.read_text(encoding="utf-8"))
        check_mail(mail, group, args.date, load_recipients(), read_mail_log())
        print(f"Aan: {', '.join(mail.to)}\nOnderwerp: {mail.subject}\n\n{mail.body}\n\nAPPROVAL HASH: {mail_hash(mail)}")
    else:
        mail = send(args.draft, group, args.approved_hash, args.date)
        print(f"SENT to {', '.join(mail.to)}: {mail.subject}")


if __name__ == "__main__":
    main()
