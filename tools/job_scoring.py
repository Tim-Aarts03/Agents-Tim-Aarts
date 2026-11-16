"""Deterministic scoring and ranking of job vacancies.

The job-scout agent extracts structured facts from a vacancy (location, hours,
domains, ...). This module turns those facts into a score, so the LLM never
does the arithmetic or the date comparison itself.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class Domain(str, Enum):
    SPORT_FOR_VULNERABLE_GROUPS = "sport_for_vulnerable_groups"
    SPORT_TECH = "sport_tech"
    MOVEMENT_SCIENCE = "movement_science"
    SPORTS_BRAND = "sports_brand"


class Location(str, Enum):
    PREFERRED_REGION = "preferred_region"  # Amsterdam / Haarlem and surroundings
    HYBRID_OR_REMOTE = "hybrid_or_remote"
    OTHER_NETHERLANDS = "other_netherlands"
    ABROAD = "abroad"


class Hours(str, Enum):
    PART_TIME = "part_time"
    FULL_TIME = "full_time"
    UNKNOWN = "unknown"


DOMAIN_POINTS: dict[Domain, int] = {
    Domain.SPORT_FOR_VULNERABLE_GROUPS: 40,
    Domain.SPORT_TECH: 30,
    Domain.MOVEMENT_SCIENCE: 30,
    Domain.SPORTS_BRAND: 25,
}
SECOND_DOMAIN_BONUS = 5
LEARNING_ENVIRONMENT_POINTS = 25
LOCATION_POINTS: dict[Location, int] = {
    Location.PREFERRED_REGION: 20,
    Location.HYBRID_OR_REMOTE: 15,
    Location.OTHER_NETHERLANDS: 5,
    Location.ABROAD: 0,
}
HOURS_POINTS: dict[Hours, int] = {
    Hours.PART_TIME: 10,
    Hours.UNKNOWN: 5,
    Hours.FULL_TIME: 5,
}
REQUIREMENTS_RISK_PENALTY = 15
MAX_SCORE = 100


class Vacancy(BaseModel):
    title: str = Field(min_length=1)
    organisation: str = Field(min_length=1)
    url: HttpUrl
    domains: list[Domain] = Field(default_factory=list)
    location: Location
    hours: Hours = Hours.UNKNOWN
    strong_learning_environment: bool = False
    requirements_risk: bool = False  # e.g. requires a master's degree or many years of experience
    deadline: date | None = None
    source: str = "web"


class ScoredVacancy(BaseModel):
    vacancy: Vacancy
    score: int
    breakdown: dict[str, int]


def is_expired(vacancy: Vacancy, today: date) -> bool:
    return vacancy.deadline is not None and vacancy.deadline < today


def score_vacancy(vacancy: Vacancy) -> ScoredVacancy:
    # Best domain counts fully; any additional domain adds a small bonus.
    domain_scores = sorted((DOMAIN_POINTS[d] for d in set(vacancy.domains)), reverse=True)
    domain = domain_scores[0] if domain_scores else 0
    if len(domain_scores) > 1:
        domain += SECOND_DOMAIN_BONUS

    breakdown = {
        "domain": domain,
        "learning_environment": LEARNING_ENVIRONMENT_POINTS if vacancy.strong_learning_environment else 0,
        "location": LOCATION_POINTS[vacancy.location],
        "hours": HOURS_POINTS[vacancy.hours],
        "requirements_risk": -REQUIREMENTS_RISK_PENALTY if vacancy.requirements_risk else 0,
    }
    score = max(0, min(MAX_SCORE, sum(breakdown.values())))
    return ScoredVacancy(vacancy=vacancy, score=score, breakdown=breakdown)


def rank_vacancies(vacancies: list[Vacancy], today: date, top_n: int = 5) -> list[ScoredVacancy]:
    """Drop expired and duplicate vacancies, score the rest, return the best `top_n`."""
    seen_urls: set[str] = set()
    scored: list[ScoredVacancy] = []
    for vacancy in vacancies:
        url = str(vacancy.url)
        if is_expired(vacancy, today) or url in seen_urls:
            continue
        seen_urls.add(url)
        scored.append(score_vacancy(vacancy))
    # Ties: earliest deadline first (more urgent), then title for a stable order.
    scored.sort(key=lambda s: (-s.score, s.vacancy.deadline or date.max, s.vacancy.title))
    return scored[:top_n]


def main() -> None:
    """CLI: `python -m tools.job_scoring vacancies.json [YYYY-MM-DD]` prints the ranked top 5 as JSON."""
    path = sys.argv[1]
    today = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    with open(path, encoding="utf-8") as f:
        vacancies = [Vacancy.model_validate(item) for item in json.load(f)]
    ranked = rank_vacancies(vacancies, today)
    print(json.dumps([s.model_dump(mode="json") for s in ranked], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
