"""Deterministic scoring and ranking of job vacancies.

The job-scout agent extracts structured facts from a vacancy (city, hours,
domains, role type, ...). This module turns those facts into a score, so the
LLM never does arithmetic, distance or date logic itself.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl

PREFERRED_PLACES_FILE = Path("knowledge/preferred_places.json")
JOB_FILTERS_FILE = Path("knowledge/job_filters.json")


class Domain(str, Enum):
    SPORT_FOR_VULNERABLE_GROUPS = "sport_for_vulnerable_groups"
    SPORT_TECH = "sport_tech"
    MOVEMENT_SCIENCE = "movement_science"
    SPORTS_BRAND = "sports_brand"


class Location(str, Enum):
    PREFERRED_REGION = "preferred_region"  # Amsterdam / Haarlem + ~10 km
    HYBRID_OR_REMOTE = "hybrid_or_remote"
    OTHER_NETHERLANDS = "other_netherlands"
    ABROAD = "abroad"
    UNKNOWN = "unknown"


class Hours(str, Enum):
    PART_TIME = "part_time"
    FULL_TIME = "full_time"
    UNKNOWN = "unknown"


class EmploymentType(str, Enum):
    JOB = "job"
    TRAINEESHIP = "traineeship"
    INTERNSHIP = "internship"  # Tim no longer wants internships: always excluded
    FREELANCE = "freelance"
    UNKNOWN = "unknown"


class RoleType(str, Enum):
    PROGRAM_COORDINATION = "program_coordination"
    RESEARCH = "research"
    POLICY_ADVICE = "policy_advice"
    MARKETING_COMMUNICATION = "marketing_communication"
    COMMERCIAL_SALES = "commercial_sales"
    OPERATIONS_LOGISTICS = "operations_logistics"
    COACHING_DELIVERY = "coaching_delivery"
    FINANCE_ADMIN = "finance_admin"
    OTHER = "other"
    UNKNOWN = "unknown"


class OrgType(str, Enum):
    FOUNDATION_NONPROFIT = "foundation_nonprofit"
    GOVERNMENT = "government"
    KNOWLEDGE_INSTITUTE = "knowledge_institute"
    SPORTS_CLUB_FEDERATION = "sports_club_federation"
    COMMERCIAL_BRAND = "commercial_brand"
    SCALEUP_TECH = "scaleup_tech"
    CARE_HEALTH = "care_health"
    OTHER = "other"
    UNKNOWN = "unknown"


class LearningEvidence(str, Enum):
    """Only counted when the vacancy text states it explicitly."""

    TRAINEESHIP_PROGRAM = "traineeship_program"
    NAMED_MENTOR_OR_COACH = "named_mentor_or_coach"
    TRAINING_BUDGET = "training_budget"
    ROTATION_ACROSS_TEAMS = "rotation_across_teams"
    DIRECT_WORK_WITH_LEADERSHIP = "direct_work_with_leadership"


class RequirementGap(str, Enum):
    """Requirements in the vacancy that Tim's profile does not meet."""

    MASTERS_DEGREE = "masters_degree"
    EXPERIENCE_3_PLUS_YEARS = "experience_3_plus_years"
    EXPERIENCE_1_2_YEARS = "experience_1_2_years"
    OTHER_HARD_REQUIREMENT = "other_hard_requirement"  # e.g. license, specific language


DOMAIN_POINTS: dict[Domain, int] = {
    Domain.SPORT_FOR_VULNERABLE_GROUPS: 40,
    Domain.SPORT_TECH: 30,
    Domain.MOVEMENT_SCIENCE: 30,
    Domain.SPORTS_BRAND: 25,
}
SECOND_DOMAIN_BONUS = 5
LEARNING_POINTS: dict[LearningEvidence, int] = {
    LearningEvidence.TRAINEESHIP_PROGRAM: 15,
    LearningEvidence.NAMED_MENTOR_OR_COACH: 8,
    LearningEvidence.TRAINING_BUDGET: 8,
    LearningEvidence.ROTATION_ACROSS_TEAMS: 8,
    LearningEvidence.DIRECT_WORK_WITH_LEADERSHIP: 8,
}
MAX_LEARNING_POINTS = 25
LOCATION_POINTS: dict[Location, int] = {
    Location.PREFERRED_REGION: 20,
    Location.HYBRID_OR_REMOTE: 15,
    Location.UNKNOWN: 8,
    Location.OTHER_NETHERLANDS: 5,
    Location.ABROAD: 0,
}
HOURS_POINTS: dict[Hours, int] = {
    Hours.PART_TIME: 10,
    Hours.FULL_TIME: 5,
    Hours.UNKNOWN: 3,
}
GAP_PENALTIES: dict[RequirementGap, int] = {
    RequirementGap.MASTERS_DEGREE: 15,
    RequirementGap.EXPERIENCE_3_PLUS_YEARS: 10,
    RequirementGap.EXPERIENCE_1_2_YEARS: 5,
    RequirementGap.OTHER_HARD_REQUIREMENT: 5,
}
ROLE_FIT_POINTS = 5
MAX_LEARNED_BONUS = 10
MAX_SCORE = 100


class Vacancy(BaseModel):
    title: str = Field(min_length=1)
    organisation: str = Field(min_length=1)
    url: HttpUrl
    city: str | None = None
    country: str = "NL"
    hybrid_or_remote: bool = False
    domains: list[Domain] = Field(default_factory=list)
    role_type: RoleType = RoleType.UNKNOWN
    org_type: OrgType = OrgType.UNKNOWN
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    hours: Hours = Hours.UNKNOWN
    learning_evidence: list[LearningEvidence] = Field(default_factory=list)
    requirement_gaps: list[RequirementGap] = Field(default_factory=list)
    deadline: date | None = None
    verified: bool = True  # False = only seen in search results, page not opened
    source: str = "web"


class JobFilters(BaseModel):
    excluded_organisations: list[str] = Field(default_factory=list)
    excluded_role_types: list[RoleType] = Field(default_factory=list)
    preferred_role_types: list[RoleType] = Field(default_factory=list)


def load_job_filters(path: Path = JOB_FILTERS_FILE) -> JobFilters:
    return JobFilters.model_validate_json(path.read_text(encoding="utf-8"))


class ScoredVacancy(BaseModel):
    vacancy: Vacancy
    score: int
    breakdown: dict[str, int]
    location: Location


def load_preferred_places(path: Path = PREFERRED_PLACES_FILE) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {place.lower() for places in data["places"].values() for place in places}


def classify_location(vacancy: Vacancy, preferred_places: set[str]) -> Location:
    if vacancy.city and vacancy.city.strip().lower() in preferred_places:
        return Location.PREFERRED_REGION
    if vacancy.hybrid_or_remote and vacancy.country.upper() == "NL":
        return Location.HYBRID_OR_REMOTE
    if vacancy.city is None:
        return Location.UNKNOWN
    return Location.OTHER_NETHERLANDS if vacancy.country.upper() == "NL" else Location.ABROAD


def vacancy_features(vacancy: Vacancy) -> list[str]:
    """Features Tim's ratings are learned on. Unknown values carry no signal, so they are skipped."""
    features = [f"domain:{d.value}" for d in sorted(set(vacancy.domains), key=lambda d: d.value)]
    for name, value in (
        ("role_type", vacancy.role_type),
        ("org_type", vacancy.org_type),
        ("employment_type", vacancy.employment_type),
    ):
        if value.value != "unknown":
            features.append(f"{name}:{value.value}")
    return features


def learned_bonus(vacancy: Vacancy, feature_bonuses: dict[str, float]) -> int:
    total = sum(feature_bonuses.get(f, 0.0) for f in vacancy_features(vacancy))
    return round(max(-MAX_LEARNED_BONUS, min(MAX_LEARNED_BONUS, total)))


def score_vacancy(
    vacancy: Vacancy,
    preferred_places: set[str],
    feature_bonuses: dict[str, float] | None = None,
    filters: JobFilters | None = None,
) -> ScoredVacancy:
    filters = filters or JobFilters()
    # Best domain counts fully; any additional domain adds a small bonus.
    domain_scores = sorted((DOMAIN_POINTS[d] for d in set(vacancy.domains)), reverse=True)
    domain = domain_scores[0] if domain_scores else 0
    if len(domain_scores) > 1:
        domain += SECOND_DOMAIN_BONUS

    evidence = set(vacancy.learning_evidence)
    if vacancy.employment_type is EmploymentType.TRAINEESHIP:
        evidence.add(LearningEvidence.TRAINEESHIP_PROGRAM)
    learning = min(MAX_LEARNING_POINTS, sum(LEARNING_POINTS[e] for e in evidence))

    location = classify_location(vacancy, preferred_places)
    breakdown = {
        "domain": domain,
        "learning_environment": learning,
        "location": LOCATION_POINTS[location],
        "hours": HOURS_POINTS[vacancy.hours],
        "role_fit": ROLE_FIT_POINTS if vacancy.role_type in filters.preferred_role_types else 0,
        "requirement_gaps": -sum(GAP_PENALTIES[g] for g in set(vacancy.requirement_gaps)),
        "learned_from_ratings": learned_bonus(vacancy, feature_bonuses or {}),
    }
    score = max(0, min(MAX_SCORE, sum(breakdown.values())))
    return ScoredVacancy(vacancy=vacancy, score=score, breakdown=breakdown, location=location)


def is_excluded(vacancy: Vacancy, today: date, filters: JobFilters | None = None) -> bool:
    filters = filters or JobFilters()
    expired = vacancy.deadline is not None and vacancy.deadline < today
    organisation = vacancy.organisation.lower()
    excluded_org = any(name.lower() in organisation for name in filters.excluded_organisations)
    return (
        expired
        or excluded_org
        or vacancy.employment_type is EmploymentType.INTERNSHIP
        or vacancy.role_type in filters.excluded_role_types
    )


def rank_vacancies(
    vacancies: list[Vacancy],
    today: date,
    preferred_places: set[str],
    feature_bonuses: dict[str, float] | None = None,
    exclude_urls: set[str] | None = None,
    filters: JobFilters | None = None,
    top_n: int = 5,
) -> list[ScoredVacancy]:
    """Drop excluded, duplicate and already-proposed vacancies; return the best `top_n`."""
    seen_urls = set(exclude_urls or ())
    scored: list[ScoredVacancy] = []
    for vacancy in vacancies:
        url = str(vacancy.url)
        if is_excluded(vacancy, today, filters) or url in seen_urls:
            continue
        seen_urls.add(url)
        scored.append(score_vacancy(vacancy, preferred_places, feature_bonuses, filters))
    # Ties: verified first, then earliest deadline (more urgent), then title for a stable order.
    scored.sort(key=lambda s: (-s.score, not s.vacancy.verified, s.vacancy.deadline or date.max, s.vacancy.title))
    return scored[:top_n]


def main() -> None:
    """CLI: `python -m tools.job_scoring candidates.json [YYYY-MM-DD]`.

    Uses learned preferences and skips vacancies already in logs/applications.csv.
    """
    from tools.applications_log import known_urls
    from tools.preference_learning import feature_bonuses_from_log

    path = sys.argv[1]
    today = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    with open(path, encoding="utf-8") as f:
        vacancies = [Vacancy.model_validate(item) for item in json.load(f)]
    ranked = rank_vacancies(
        vacancies,
        today,
        load_preferred_places(),
        feature_bonuses=feature_bonuses_from_log(),
        exclude_urls=known_urls(),
        filters=load_job_filters(),
    )
    print(json.dumps([s.model_dump(mode="json") for s in ranked], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
