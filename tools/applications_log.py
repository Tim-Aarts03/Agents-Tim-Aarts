"""Application log (logs/applications.csv): read before a run, update after.

Prevents proposing the same vacancy twice, stores Tim's 1–5 ratings with the
vacancy's features (for preference learning) and records outcomes so the
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
FEATURE_SEPARATOR = ";"


class Status(str, Enum):
    PROPOSED = "proposed"  # shown in the Friday overview
    SELECTED = "selected"  # Tim chose it; letter in progress
    SENT = "sent"  # Tim sent the application
    INVITED = "invited"
    REJECTED = "rejected"
    NO_RESPONSE = "no_response"
    SKIPPED = "skipped"  # proposed but not chosen
    TRAINING = "training"  # fictional vacancy, only used to learn Tim's preferences


class Application(BaseModel):
    url: str = Field(min_length=1)  # vacancy URL, or "seed:<slug>" for historical applications
    organisation: str
    title: str
    status: Status
    date_proposed: date
    date_updated: date
    score: int | None = None
    rating: int | None = Field(default=None, ge=1, le=5)  # the role itself (or the vacancy as a whole)
    # Tim judges the organisation separately from the role (e.g. ASICS: company 5, merchandise role 3).
    org_rating: int | None = Field(default=None, ge=1, le=5)
    rating_reason: str = ""
    features: str = ""  # FEATURE_SEPARATOR-joined output of tools.job_scoring.vacancy_features
    letter_file: str = ""
    feedback: str = ""

    def feature_list(self) -> list[str]:
        return [f for f in self.features.split(FEATURE_SEPARATOR) if f]


FIELDS = list(Application.model_fields)
OPTIONAL_INT_FIELDS = ("score", "rating", "org_rating")


def read_log(path: Path = DEFAULT_LOG_PATH) -> list[Application]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    apps = []
    for row in rows:
        # Drop columns that are missing or empty, so older log files and empty cells fall back to defaults.
        clean = {k: v for k, v in row.items() if k in FIELDS and v not in (None, "")}
        apps.append(Application.model_validate(clean))
    return apps


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


def update_application(url: str, today: date, path: Path = DEFAULT_LOG_PATH, **changes) -> Application:
    """Update fields of one application (e.g. status, rating, rating_reason, letter_file, feedback)."""
    log = read_log(path)
    for i, app in enumerate(log):
        if app.url == url:
            updated = Application.model_validate({**app.model_dump(), **changes, "date_updated": today})
            log[i] = updated
            write_log(log, path)
            return updated
    raise KeyError(f"No application with url {url!r}")


def update_status(url: str, status: Status, today: date, path: Path = DEFAULT_LOG_PATH, **changes) -> Application:
    return update_application(url, today, path, status=status, **changes)


def rate(url: str, rating: int, reason: str, today: date, path: Path = DEFAULT_LOG_PATH,
         org_rating: int | None = None) -> Application:
    """Store Tim's role rating and, if he gave one, a separate organisation rating."""
    changes: dict = {"rating": rating, "rating_reason": reason}
    if org_rating is not None:
        changes["org_rating"] = org_rating
    return update_application(url, today, path, **changes)


def main() -> None:
    """CLI:
    `python -m tools.applications_log`                         list all applications
    `python -m tools.applications_log urls`                    print known vacancy URLs
    `python -m tools.applications_log rate <url> <1-5> [--org <1-5>] [reason]`
        store Tim's role rating and optionally a separate organisation rating
    """
    args = sys.argv[1:]
    if args[:1] == ["urls"]:
        for url in sorted(known_urls()):
            print(url)
    elif args[:1] == ["rate"]:
        rest = args[3:]
        org_rating = None
        if "--org" in rest:
            i = rest.index("--org")
            org_rating = int(rest[i + 1])
            rest = rest[:i] + rest[i + 2:]
        app = rate(args[1], int(args[2]), " ".join(rest), date.today(), org_rating=org_rating)
        org = f", organisatie {app.org_rating}" if app.org_rating is not None else ""
        print(f"Rated {app.organisation} — {app.title}: functie {app.rating}{org}")
    else:
        for app in read_log():
            rating = app.rating if app.rating is not None else "-"
            org = app.org_rating if app.org_rating is not None else "-"
            print(f"{app.date_updated} | {app.status.value:<11} | role {rating} org {org} | {app.organisation} — {app.title}")


if __name__ == "__main__":
    main()
