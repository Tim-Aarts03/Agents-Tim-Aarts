"""Networking events: scoring, the event log and learning from Tim's ratings.

The event-scout agent extracts structured facts from an event page (date, city,
topics, price, who attends). This module does all arithmetic and date logic:
the score, the search window, the monthly "did Tim go yet?" check and the
learned bonus from Tim's 1–5 ratings.

Tim does not know yet what he likes (2026-11-20), so the fixed weights are small
and the learned bonus is large: his ratings should drive the ranking quickly.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl

from tools.job_scoring import JobFilters, load_job_filters, load_preferred_places

DEFAULT_LOG_PATH = Path("logs/events.csv")
FEATURE_SEPARATOR = ";"
DEFAULT_WINDOW_DAYS = 42  # six weeks ahead: enough to plan one event per month
DEFAULT_TOP_N = 5


class EventType(str, Enum):
    NETWORKING = "networking"  # borrel, drinks, network evening
    CONFERENCE = "conference"  # congress, symposium, summit
    CAREER_EVENT = "career_event"  # career fair, traineeship day, recruitment event
    MEETUP = "meetup"
    WORKSHOP = "workshop"  # masterclass, training session
    WEBINAR = "webinar"
    SPORTS_EVENT = "sports_event"  # sports event with a networking part
    OTHER = "other"
    UNKNOWN = "unknown"


class Topic(str, Enum):
    SPORT_FOR_VULNERABLE_GROUPS = "sport_for_vulnerable_groups"
    SPORT_POLICY = "sport_policy"
    SOCIAL_IMPACT = "social_impact"
    SPORTS_BUSINESS = "sports_business"
    SPORT_TECH = "sport_tech"
    MOVEMENT_SCIENCE = "movement_science"
    CAREERS_TRAINEESHIPS = "careers_traineeships"
    ENTREPRENEURSHIP = "entrepreneurship"


class Audience(str, Enum):
    STUDENTS_STARTERS = "students_starters"
    PROFESSIONALS = "professionals"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class NetworkEvidence(str, Enum):
    """Only counted when the event page states it explicitly."""

    TARGET_ORGANISATIONS_PRESENT = "target_organisations_present"  # dream employers / policy organisations
    RECRUITERS_PRESENT = "recruiters_present"
    DECISION_MAKERS_SPEAKING = "decision_makers_speaking"  # directors, policy makers, founders on stage
    DEDICATED_NETWORKING_TIME = "dedicated_networking_time"  # borrel, speed-dating, matchmaking
    SMALL_GROUP = "small_group"  # max ~50 participants stated


class Location(str, Enum):
    PREFERRED_REGION = "preferred_region"
    OTHER_NETHERLANDS = "other_netherlands"
    ONLINE = "online"
    ABROAD = "abroad"
    UNKNOWN = "unknown"


class PriceBand(str, Enum):
    FREE = "free"
    UNDER_50 = "under_50"
    FROM_50_TO_150 = "50_to_150"
    OVER_150 = "over_150"
    UNKNOWN = "unknown"


TOPIC_POINTS: dict[Topic, int] = {
    Topic.SPORT_FOR_VULNERABLE_GROUPS: 15,
    Topic.SPORT_POLICY: 12,
    Topic.SOCIAL_IMPACT: 10,
    Topic.SPORTS_BUSINESS: 10,
    Topic.CAREERS_TRAINEESHIPS: 10,
    Topic.MOVEMENT_SCIENCE: 8,
    Topic.SPORT_TECH: 6,
    Topic.ENTREPRENEURSHIP: 4,
}
EXTRA_TOPIC_BONUS = 3
NETWORK_POINTS: dict[NetworkEvidence, int] = {
    NetworkEvidence.TARGET_ORGANISATIONS_PRESENT: 8,
    NetworkEvidence.RECRUITERS_PRESENT: 6,
    NetworkEvidence.DECISION_MAKERS_SPEAKING: 5,
    NetworkEvidence.DEDICATED_NETWORKING_TIME: 5,
    NetworkEvidence.SMALL_GROUP: 3,
}
MAX_NETWORK_POINTS = 20
# Meeting people face to face is the point, so online scores low.
LOCATION_POINTS: dict[Location, int] = {
    Location.PREFERRED_REGION: 10,
    Location.OTHER_NETHERLANDS: 6,
    Location.UNKNOWN: 4,
    Location.ABROAD: 2,
    Location.ONLINE: 0,
}
AUDIENCE_POINTS: dict[Audience, int] = {
    Audience.STUDENTS_STARTERS: 3,
    Audience.MIXED: 3,
    Audience.PROFESSIONALS: 2,
    Audience.UNKNOWN: 1,
}
MAX_LEARNED_BONUS = 25
MAX_SCORE = 100


class Event(BaseModel):
    title: str = Field(min_length=1)
    organiser: str = Field(min_length=1)
    url: HttpUrl
    start_date: date
    end_date: date | None = None
    start_time: str | None = None  # as written on the page, e.g. "19:00"
    city: str | None = None
    country: str = "NL"
    online: bool = False
    event_type: EventType = EventType.UNKNOWN
    topics: list[Topic] = Field(default_factory=list)
    audience: Audience = Audience.UNKNOWN
    network_evidence: list[NetworkEvidence] = Field(default_factory=list)
    price_eur: float | None = Field(default=None, ge=0)  # cheapest regular ticket; None = not stated
    registration_deadline: date | None = None
    sold_out: bool = False  # "volgeboekt", "uitverkocht", registration closed
    language: str = "nl"
    verified: bool = True  # False = only seen in search results, page not opened
    source: str = "web"


def price_band(price_eur: float | None) -> PriceBand:
    if price_eur is None:
        return PriceBand.UNKNOWN
    if price_eur == 0:
        return PriceBand.FREE
    if price_eur < 50:
        return PriceBand.UNDER_50
    if price_eur <= 150:
        return PriceBand.FROM_50_TO_150
    return PriceBand.OVER_150


def classify_location(event: Event, preferred_places: set[str]) -> Location:
    if event.online:
        return Location.ONLINE
    if event.city and event.city.strip().lower() in preferred_places:
        return Location.PREFERRED_REGION
    if event.city is None:
        return Location.UNKNOWN
    return Location.OTHER_NETHERLANDS if event.country.upper() == "NL" else Location.ABROAD


def event_features(event: Event, preferred_places: set[str]) -> list[str]:
    """Features Tim's ratings are learned on. Unknown values carry no signal, so they are skipped."""
    features = [f"topic:{t.value}" for t in sorted(set(event.topics), key=lambda t: t.value)]
    for name, value in (
        ("event_type", event.event_type),
        ("audience", event.audience),
        ("location", classify_location(event, preferred_places)),
        ("price", price_band(event.price_eur)),
    ):
        if value.value != "unknown":
            features.append(f"{name}:{value.value}")
    return features


# --- Event log -------------------------------------------------------------------------------


class Status(str, Enum):
    PROPOSED = "proposed"  # shown in the Friday overview
    INTERESTED = "interested"  # Tim wants to go; registers himself
    REGISTERED = "registered"  # Tim registered
    ATTENDED = "attended"
    SKIPPED = "skipped"  # proposed but not chosen
    TRAINING = "training"  # fictional event, only used to learn Tim's preferences


GOING_STATUSES = (Status.REGISTERED, Status.ATTENDED)


class LoggedEvent(BaseModel):
    url: str = Field(min_length=1)
    organiser: str
    title: str
    event_date: date
    status: Status
    date_proposed: date
    date_updated: date
    score: int | None = None
    price_eur: float | None = None
    rating: int | None = Field(default=None, ge=1, le=5)  # how interesting it looks beforehand
    # Real experience beats a first impression, so learning prefers this rating when Tim gives it.
    after_rating: int | None = Field(default=None, ge=1, le=5)
    rating_reason: str = ""
    features: str = ""
    feedback: str = ""  # after the event: who Tim met, what it brought

    def feature_list(self) -> list[str]:
        return [f for f in self.features.split(FEATURE_SEPARATOR) if f]

    def learning_rating(self) -> int | None:
        return self.after_rating if self.after_rating is not None else self.rating


FIELDS = list(LoggedEvent.model_fields)


def read_log(path: Path = DEFAULT_LOG_PATH) -> list[LoggedEvent]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [
        LoggedEvent.model_validate({k: v for k, v in row.items() if k in FIELDS and v not in (None, "")})
        for row in rows
    ]


def write_log(events: list[LoggedEvent], path: Path = DEFAULT_LOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for event in events:
            row = event.model_dump(mode="json")
            writer.writerow({k: "" if row[k] is None else row[k] for k in FIELDS})


def known_urls(path: Path = DEFAULT_LOG_PATH) -> set[str]:
    return {e.url for e in read_log(path)}


def add_proposed(event: LoggedEvent, path: Path = DEFAULT_LOG_PATH) -> bool:
    """Add an event; returns False if its URL is already in the log."""
    log = read_log(path)
    if any(existing.url == event.url for existing in log):
        return False
    log.append(event)
    write_log(log, path)
    return True


def update_event(url: str, today: date, path: Path = DEFAULT_LOG_PATH, **changes) -> LoggedEvent:
    log = read_log(path)
    for i, event in enumerate(log):
        if event.url == url:
            updated = LoggedEvent.model_validate({**event.model_dump(), **changes, "date_updated": today})
            log[i] = updated
            write_log(log, path)
            return updated
    raise KeyError(f"No event with url {url!r}")


# --- Learning from ratings -------------------------------------------------------------------

MIN_RATINGS = 3
NEUTRAL_RATING = 3.0
POINTS_PER_RATING_STEP = 4.0  # avg 5 -> +8, avg 1 -> -8 per feature


def feature_stats(events: list[LoggedEvent]) -> dict[str, list[int]]:
    ratings: dict[str, list[int]] = defaultdict(list)
    for event in events:
        rating = event.learning_rating()
        if rating is None:
            continue
        for feature in event.feature_list():
            ratings[feature].append(rating)
    return dict(ratings)


def feature_bonuses(events: list[LoggedEvent]) -> dict[str, float]:
    return {
        feature: (sum(r) / len(r) - NEUTRAL_RATING) * POINTS_PER_RATING_STEP
        for feature, r in feature_stats(events).items()
        if len(r) >= MIN_RATINGS
    }


def learning_summary(events: list[LoggedEvent]) -> list[str]:
    lines = []
    stats = feature_stats(events)
    for feature, ratings in sorted(stats.items(), key=lambda kv: -abs(sum(kv[1]) / len(kv[1]) - NEUTRAL_RATING)):
        avg = sum(ratings) / len(ratings)
        status = "actief" if len(ratings) >= MIN_RATINGS else f"nog {MIN_RATINGS - len(ratings)} beoordeling(en) nodig"
        lines.append(f"{feature}: gemiddeld {avg:.1f} uit {len(ratings)} ({status})")
    return lines


# --- Scoring and ranking ---------------------------------------------------------------------


class ScoredEvent(BaseModel):
    event: Event
    score: int
    breakdown: dict[str, int]
    location: Location
    price_band: PriceBand
    features: list[str]


def learned_bonus(features: list[str], bonuses: dict[str, float]) -> int:
    total = sum(bonuses.get(f, 0.0) for f in features)
    return round(max(-MAX_LEARNED_BONUS, min(MAX_LEARNED_BONUS, total)))


def score_event(event: Event, preferred_places: set[str], bonuses: dict[str, float] | None = None) -> ScoredEvent:
    topic_scores = sorted((TOPIC_POINTS[t] for t in set(event.topics)), reverse=True)
    topic = (topic_scores[0] if topic_scores else 0) + EXTRA_TOPIC_BONUS * max(0, len(topic_scores) - 1)
    network = min(MAX_NETWORK_POINTS, sum(NETWORK_POINTS[e] for e in set(event.network_evidence)))
    location = classify_location(event, preferred_places)
    features = event_features(event, preferred_places)
    breakdown = {
        "topic": topic,
        "network": network,
        "location": LOCATION_POINTS[location],
        "audience": AUDIENCE_POINTS[event.audience],
        "learned_from_ratings": learned_bonus(features, bonuses or {}),
    }
    score = max(0, min(MAX_SCORE, sum(breakdown.values())))
    return ScoredEvent(
        event=event, score=score, breakdown=breakdown, location=location,
        price_band=price_band(event.price_eur), features=features,
    )


def is_excluded(event: Event, today: date, window_days: int, filters: JobFilters | None = None) -> bool:
    filters = filters or JobFilters()
    organiser = event.organiser.lower()
    return (
        event.start_date < today
        or event.start_date > today + timedelta(days=window_days)
        or event.sold_out
        or (event.registration_deadline is not None and event.registration_deadline < today)
        or any(name.lower() in organiser for name in filters.excluded_organisations)
    )


def rank_events(
    events: list[Event],
    today: date,
    preferred_places: set[str],
    bonuses: dict[str, float] | None = None,
    exclude_urls: set[str] | None = None,
    filters: JobFilters | None = None,
    window_days: int = DEFAULT_WINDOW_DAYS,
    top_n: int = DEFAULT_TOP_N,
) -> list[ScoredEvent]:
    """Drop past, too-far-ahead, closed, excluded and already-proposed events; return the best `top_n`."""
    seen = set(exclude_urls or ())
    scored = []
    for event in events:
        url = str(event.url)
        if url in seen or is_excluded(event, today, window_days, filters):
            continue
        seen.add(url)
        scored.append(score_event(event, preferred_places, bonuses))
    # Ties: verified first, then the soonest event (needs a decision first), then title.
    scored.sort(key=lambda s: (-s.score, not s.event.verified, s.event.start_date, s.event.title))
    return scored[:top_n]


# --- One event per month ---------------------------------------------------------------------


def month_status(events: list[LoggedEvent], today: date) -> dict:
    """Has Tim registered for or attended an event this calendar month?"""
    this_month = [
        e for e in events
        if e.status in GOING_STATUSES and (e.event_date.year, e.event_date.month) == (today.year, today.month)
    ]
    upcoming = sorted((e for e in events if e.status in GOING_STATUSES and e.event_date >= today),
                      key=lambda e: e.event_date)
    return {
        "month": f"{today.year}-{today.month:02d}",
        "done_this_month": bool(this_month),
        "this_month": [f"{e.event_date} {e.title} ({e.organiser}, {e.status.value})" for e in this_month],
        "upcoming": [f"{e.event_date} {e.title} ({e.organiser}, {e.status.value})" for e in upcoming],
    }


# --- CLI -------------------------------------------------------------------------------------


def main() -> None:
    """CLI:
    `python -m tools.events score candidates.json [YYYY-MM-DD]`   rank events (JSON)
    `python -m tools.events log-ranked ranked.json [YYYY-MM-DD]`  add ranked events to the log as proposed
    `python -m tools.events list`                                 show the event log
    `python -m tools.events learned`                              what has been learned from ratings
    `python -m tools.events month [YYYY-MM-DD]`                   has Tim been to an event this month?
    `python -m tools.events rate <url> <1-5> [reason]`            Tim's rating beforehand
    `python -m tools.events after <url> <1-5> [feedback]`         Tim's rating after attending (sets attended)
    `python -m tools.events status <url> <status>`                e.g. interested, registered, skipped
    """
    args = sys.argv[1:]
    command = args[0] if args else "list"
    today = date.today()
    if command == "score":
        if len(args) > 2:
            today = date.fromisoformat(args[2])
        events = [Event.model_validate(item) for item in json.loads(Path(args[1]).read_text(encoding="utf-8"))]
        ranked = rank_events(
            events, today, load_preferred_places(),
            bonuses=feature_bonuses(read_log()), exclude_urls=known_urls(), filters=load_job_filters(),
        )
        print(json.dumps([s.model_dump(mode="json") for s in ranked], indent=2, ensure_ascii=False))
    elif command == "log-ranked":
        if len(args) > 2:
            today = date.fromisoformat(args[2])
        for item in json.loads(Path(args[1]).read_text(encoding="utf-8")):
            scored = ScoredEvent.model_validate(item)
            added = add_proposed(LoggedEvent(
                url=str(scored.event.url), organiser=scored.event.organiser, title=scored.event.title,
                event_date=scored.event.start_date, status=Status.PROPOSED, date_proposed=today,
                date_updated=today, score=scored.score, price_eur=scored.event.price_eur,
                features=FEATURE_SEPARATOR.join(scored.features),
            ))
            print(f"{'added' if added else 'already in log'}: {scored.event.title}")
    elif command == "learned":
        lines = learning_summary(read_log())
        print("\n".join(lines) if lines else "Nog geen beoordelingen.")
    elif command == "month":
        if len(args) > 1:
            today = date.fromisoformat(args[1])
        print(json.dumps(month_status(read_log(), today), indent=2, ensure_ascii=False))
    elif command == "rate":
        e = update_event(args[1], today, rating=int(args[2]), rating_reason=" ".join(args[3:]))
        print(f"Rated {e.title}: {e.rating}")
    elif command == "after":
        e = update_event(args[1], today, status=Status.ATTENDED, after_rating=int(args[2]), feedback=" ".join(args[3:]))
        print(f"Attended {e.title}: {e.after_rating}")
    elif command == "status":
        e = update_event(args[1], today, status=Status(args[2]))
        print(f"{e.title}: {e.status.value}")
    else:
        log = read_log()
        if not log:
            print("Nog geen events gelogd.")
        for e in log:
            rating = e.rating if e.rating is not None else "-"
            after = e.after_rating if e.after_rating is not None else "-"
            print(f"{e.event_date} | {e.status.value:<10} | voor {rating} na {after} | {e.organiser} — {e.title}")


if __name__ == "__main__":
    main()
