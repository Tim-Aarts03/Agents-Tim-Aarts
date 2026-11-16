"""Application log (logs/applications.csv): read before a run, update after.

Prevents proposing the same vacancy twice and records outcomes so the
letter style can improve over time.
"""

from __future__ import annotations

import csv
import sys
from datetime import date
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

DEFAULT_LOG_PATH = Path("logs/applications.csv")


class Status(str, Enum):
    PROPOSED = "proposed"  # shown in the Friday top 5
    SELECTED = "selected"  # Tim chose it; letter in progress
    SENT = "sent"  # Tim sent the application
    INVITED = "invited"
    REJECTED = "rejected"
    NO_RESPONSE = "no_response"
    SKIPPED = "skipped"  # proposed but not chosen


class Application(BaseModel):
    url: str = Field(min_length=1)
    organisation: str
    title: str
    status: Status
    date_proposed: date
    date_updated: date
    score: int | None = None
    letter_file: str = ""
    feedback: str = ""


FIELDS = list(Application.model_fields)


def read_log(path: Path = DEFAULT_LOG_PATH) -> list[Application]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    # CSV has no null: an empty score cell means "no score".
    return [Application.model_validate({**row, "score": row["score"] or None}) for row in rows]


def write_log(applications: list[Application], path: Path = DEFAULT_LOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for app in applications:
            row = app.model_dump(mode="json")
            writer.writerow({k: "" if row[k] is None else row[k] for k in FIELDS})


def known_urls(path: Path = DEFAULT_LOG_PATH) -> set[str]:
    return {app.url for app in read_log(path)}


def add_proposed(app: Application, path: Path = DEFAULT_LOG_PATH) -> bool:
    """Add a vacancy; returns False if its URL is already in the log."""
    log = read_log(path)
    if any(existing.url == app.url for existing in log):
        return False
    log.append(app)
    write_log(log, path)
    return True


def update_status(
    url: str,
    status: Status,
    today: date,
    path: Path = DEFAULT_LOG_PATH,
    letter_file: str | None = None,
    feedback: str | None = None,
) -> Application:
    log = read_log(path)
    for i, app in enumerate(log):
        if app.url == url:
            changes: dict = {"status": status, "date_updated": today}
            if letter_file is not None:
                changes["letter_file"] = letter_file
            if feedback is not None:
                changes["feedback"] = feedback
            log[i] = app.model_copy(update=changes)
            write_log(log, path)
            return log[i]
    raise KeyError(f"No application with url {url!r}")


def main() -> None:
    """CLI: `python -m tools.applications_log urls` prints all known vacancy URLs."""
    if len(sys.argv) > 1 and sys.argv[1] == "urls":
        for url in sorted(known_urls()):
            print(url)
    else:
        for app in read_log():
            print(f"{app.date_updated} | {app.status.value:<11} | {app.organisation} — {app.title}")


if __name__ == "__main__":
    main()
