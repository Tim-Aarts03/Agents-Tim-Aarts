"""Compose the weekly bootcamp mails deterministically.

The LLM only writes the short promotional pitch; dates, greetings, link and
fixed texts are filled in here so they can never be wrong.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, timedelta
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl, field_validator

from tools.bootcamp_weather import WeatherAdvice

RECIPIENTS_FILE = Path("knowledge/private_mail_recipients.json")
MAIL_LOG = Path("logs/bootcamp_mails.csv")
LOG_FIELDS = ["send_date", "session_date", "kind", "group", "pitch", "tim_feedback"]
SIGNATURE = "Met vriendelijke groet,\nTim Aarts"
SESSION_TIME = "16:15"
TUESDAY = 1  # date.weekday(): Monday = 0
MAX_PITCH_SENTENCES = 3
MONTHS_NL = [
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december",
]


class Group(str, Enum):
    HOF_VAN_JACOB = "hof_van_jacob"
    JACOB_KLINIEK = "jacob_kliniek"


GREETINGS: dict[Group, str] = {
    Group.HOF_VAN_JACOB: "Beste collega's,",
    Group.JACOB_KLINIEK: "Goedemiddag team Jacob Kliniek,",
}


class Mail(BaseModel):
    to: list[str]
    subject: str
    body: str


class Pitch(BaseModel):
    text: str = Field(min_length=10, max_length=400)

    @field_validator("text")
    @classmethod
    def at_most_three_sentences(cls, value: str) -> str:
        sentences = [s for s in value.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        if len(sentences) > MAX_PITCH_SENTENCES:
            raise ValueError(f"pitch has {len(sentences)} sentences; max is {MAX_PITCH_SENTENCES}")
        return value.strip()


def next_tuesday(after: date) -> date:
    """The first Tuesday strictly after `after` (a mail sent on a Tuesday promotes next week's session)."""
    days = (TUESDAY - after.weekday()) % 7 or 7
    return after + timedelta(days=days)


def dutch_date(d: date) -> str:
    return f"{d.day} {MONTHS_NL[d.month - 1]}"


def load_recipients(path: Path = RECIPIENTS_FILE) -> dict[Group, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {Group(k): v for k, v in data.items() if k in Group._value2member_map_}


def promo_mail(group: Group, pitch: Pitch, link: HttpUrl | str, send_date: date, recipients: list[str]) -> Mail:
    session = next_tuesday(send_date)
    body = "\n\n".join(
        [
            GREETINGS[group],
            pitch.text,
            f"Dinsdag {dutch_date(session)} om {SESSION_TIME} staat er een nieuwe beweegsessie op het balkon van team 2. "
            "Meld je aan via de onderstaande link:",
            str(link),
            "Tot dinsdag!",
            SIGNATURE,
        ]
    )
    return Mail(to=recipients, subject=f"Beweegsessie dinsdag {dutch_date(session)} – meld je aan", body=body)


def reminder_mail(session_date: date, advice: WeatherAdvice, recipients: list[str]) -> Mail:
    lines = [
        "!Reminder!",
        "Wat leuk dat jij je hebt aangemeld voor de beweegsessie van morgen.\n"
        "Vergeet je sportspullen niet mee te nemen.",
    ]
    if advice.lines:
        lines.append("\n".join(advice.lines))
    lines += ["Tot morgen!", SIGNATURE]
    return Mail(
        to=recipients,
        subject=f"Reminder: beweegsessie morgen ({dutch_date(session_date)}) om {SESSION_TIME}",
        body="\n\n".join(lines),
    )


def read_mail_log(path: Path = MAIL_LOG) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def log_mail(send_date: date, kind: str, group: str, pitch: str, path: Path = MAIL_LOG) -> None:
    """Append a sent/drafted mail. Contains no recipient addresses or participant names."""
    rows = read_mail_log(path)
    rows.append(
        {"send_date": send_date.isoformat(), "session_date": next_tuesday(send_date).isoformat(),
         "kind": kind, "group": group, "pitch": pitch, "tim_feedback": ""}
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """CLI (prints the mail as JSON; never sends anything):
    python -m tools.bootcamp_mail promo --group hof_van_jacob --pitch "..." --link URL [--date YYYY-MM-DD]
    python -m tools.bootcamp_mail reminder --to a@x.nl b@y.nl [--date YYYY-MM-DD] [--offline]
    """
    from tools.bootcamp_weather import advice_for_session, fetch_session_forecast

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="kind", required=True)
    p = sub.add_parser("promo")
    p.add_argument("--group", required=True, choices=[g.value for g in Group])
    p.add_argument("--pitch", required=True)
    p.add_argument("--link", required=True)
    p.add_argument("--date", type=date.fromisoformat, default=date.today())
    r = sub.add_parser("reminder")
    r.add_argument("--to", nargs="*", default=[])
    r.add_argument("--date", type=date.fromisoformat, default=date.today(), help="date the reminder is sent (Monday)")
    r.add_argument("--offline", action="store_true", help="skip the weather forecast")
    args = parser.parse_args()

    if args.kind == "promo":
        group = Group(args.group)
        recipients = load_recipients().get(group, []) if RECIPIENTS_FILE.exists() else []
        mail = promo_mail(group, Pitch(text=args.pitch), args.link, args.date, recipients)
    else:
        session = next_tuesday(args.date)
        forecast = None if args.offline else fetch_session_forecast(session)
        mail = reminder_mail(session, advice_for_session(forecast), args.to)
    print(mail.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
