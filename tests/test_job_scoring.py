from datetime import date

import pytest
from pydantic import ValidationError

from tools.job_scoring import (
    EmploymentType,
    Hours,
    LearningEvidence,
    Location,
    RequirementGap,
    Vacancy,
    JobFilters,
    classify_location,
    is_excluded,
    load_job_filters,
    load_preferred_places,
    rank_vacancies,
    score_vacancy,
    vacancy_features,
)

TODAY = date(2026, 11, 20)
PLACES = {"amsterdam", "haarlem", "heemstede"}


def make(title: str = "Job", **overrides) -> Vacancy:
    data = {
        "title": title,
        "organisation": "Org",
        "url": f"https://example.org/{title.replace(' ', '-')}",
        "city": "Amsterdam",
    }
    data.update(overrides)
    return Vacancy(**data)


def score(v: Vacancy, bonuses: dict[str, float] | None = None):
    return score_vacancy(v, PLACES, bonuses)


def test_best_single_domain_vacancy():
    v = make(
        domains=["sport_for_vulnerable_groups"],
        employment_type="traineeship",
        learning_evidence=["named_mentor_or_coach"],
        hours="part_time",
        impact_scale="international",
    )
    result = score(v)
    assert result.breakdown == {
        "domain": 25,
        "learning_environment": 23,  # traineeship 15 + mentor 8
        "location": 10,
        "impact_scale": 20,
        "hours": 5,
        "role_fit": 0,
        "good_cause_role": 0,
        "requirement_gaps": 0,
        "startup_app_penalty": 0,
        "learned_from_ratings": 0,
    }
    assert result.score == 83


def test_second_domain_bonus_and_cap_at_100():
    v = make(
        domains=["sport_tech", "sport_for_vulnerable_groups"],
        learning_evidence=["traineeship_program", "training_budget", "named_mentor_or_coach"],
        hours="part_time",
        impact_scale="international",
        role_type="research",
    )
    result = score(v, {"role_type:research": 5.0, "impact_scale:international": 5.0, "domain:sport_tech": 5.0})
    assert result.breakdown["domain"] == 30
    assert result.breakdown["learning_environment"] == 25  # capped
    assert result.score == 100


def test_traineeship_evidence_is_not_counted_twice():
    v = make(employment_type="traineeship", learning_evidence=["traineeship_program"])
    assert score(v).breakdown["learning_environment"] == 15


@pytest.mark.parametrize(
    ("city", "hybrid", "country", "expected"),
    [
        ("Heemstede", False, "NL", Location.PREFERRED_REGION),
        ("  haarlem ", False, "NL", Location.PREFERRED_REGION),
        ("Utrecht", True, "NL", Location.HYBRID_OR_REMOTE),
        ("Utrecht", False, "NL", Location.OTHER_NETHERLANDS),
        (None, False, "NL", Location.UNKNOWN),
        ("Berlin", False, "DE", Location.ABROAD),
    ],
)
def test_classify_location(city, hybrid, country, expected):
    v = make(city=city, hybrid_or_remote=hybrid, country=country)
    assert classify_location(v, PLACES) is expected


def test_unknown_hours_score_lower_than_full_time():
    assert score(make(hours=Hours.UNKNOWN)).score < score(make(hours=Hours.FULL_TIME)).score


def test_requirement_gaps_are_graded_and_score_never_below_zero():
    master = score(make(requirement_gaps=["masters_degree"])).breakdown["requirement_gaps"]
    junior = score(make(requirement_gaps=["experience_1_2_years"])).breakdown["requirement_gaps"]
    assert master == -15 and junior == -5
    v = make(city="Berlin", country="DE", hours="full_time", requirement_gaps=list(RequirementGap))
    assert score(v).score == 0


def test_learned_bonus_is_capped():
    v = make(domains=["sport_tech"], role_type="research", org_type="scaleup_tech")
    bonuses = {"domain:sport_tech": 5.0, "role_type:research": 5.0, "org_type:scaleup_tech": 5.0}
    assert score(v, bonuses).breakdown["learned_from_ratings"] == 10
    negative = {k: -5.0 for k in bonuses}
    assert score(v, negative).breakdown["learned_from_ratings"] == -10


def test_vacancy_features_skip_unknowns():
    v = make(domains=["sport_tech", "sport_tech"], org_type="government")
    assert vacancy_features(v) == ["domain:sport_tech", "org_type:government"]
    v = make(impact_scale="national")
    assert vacancy_features(v) == ["impact_scale:national"]


@pytest.mark.parametrize(
    ("overrides", "excluded"),
    [
        ({}, False),
        ({"deadline": date(2026, 11, 19)}, True),
        ({"deadline": TODAY}, False),
        ({"employment_type": EmploymentType.INTERNSHIP}, True),
        ({"employment_type": EmploymentType.TRAINEESHIP}, False),
    ],
)
def test_exclusions(overrides, excluded):
    assert is_excluded(make(**overrides), TODAY) is excluded


def test_rank_drops_excluded_duplicates_and_known_urls():
    vacancies = [make(f"job {i}", domains=["sport_tech"]) for i in range(8)]
    vacancies.append(make("old", domains=["sport_for_vulnerable_groups"], deadline=date(2026, 1, 1)))
    vacancies.append(make("job 0", domains=["sport_for_vulnerable_groups"]))  # duplicate URL
    ranked = rank_vacancies(vacancies, TODAY, PLACES, exclude_urls={"https://example.org/job-1"})
    titles = [s.vacancy.title for s in ranked]
    assert len(ranked) == 5
    assert "old" not in titles and "job 1" not in titles
    assert titles.count("job 0") == 1


def test_rank_tiebreak_verified_then_deadline():
    best = make("best", domains=["sport_for_vulnerable_groups"])
    unverified = make("unverified", domains=["sport_tech"], verified=False)
    tie_late = make("tie late", domains=["sport_tech"], deadline=date(2026, 12, 31))
    tie_early = make("tie early", domains=["sport_tech"], deadline=date(2026, 12, 1))
    ranked = rank_vacancies([unverified, tie_late, tie_early, best], TODAY, PLACES)
    assert [s.vacancy.title for s in ranked] == ["best", "tie early", "tie late", "unverified"]


def test_invalid_input_is_rejected():
    with pytest.raises(ValidationError):
        make(url="not a url")
    with pytest.raises(ValidationError):
        make(domains=["football_betting"])
    with pytest.raises(ValidationError):
        make(learning_evidence=["great team vibes"])


def test_real_preferred_places_file_is_valid():
    places = load_preferred_places()
    assert {"amsterdam", "haarlem", "heemstede"} <= places
    assert LearningEvidence.TRAINEESHIP_PROGRAM.value == "traineeship_program"


FILTERS = JobFilters(
    excluded_organisations=["FIFA", "Red Bull"],
    excluded_role_types=["coaching_delivery"],
    preferred_role_types=["program_coordination", "policy_advice"],
    penalised_org_types={"scaleup_tech": 10},
    app_product_penalty=10,
)


@pytest.mark.parametrize(
    ("overrides", "excluded"),
    [
        ({"organisation": "FIFA Foundation"}, True),
        ({"organisation": "red bull Nederland"}, True),
        ({"organisation": "UEFA Foundation for Children"}, False),
        ({"role_type": "coaching_delivery"}, True),
        ({"role_type": "policy_advice"}, False),
    ],
)
def test_job_filters_exclusions(overrides, excluded):
    assert is_excluded(make(**overrides), TODAY, FILTERS) is excluded


def test_preferred_role_type_gets_role_fit_points():
    assert score_vacancy(make(role_type="program_coordination"), PLACES, filters=FILTERS).breakdown["role_fit"] == 5
    assert score_vacancy(make(role_type="research"), PLACES, filters=FILTERS).breakdown["role_fit"] == 0


def test_good_cause_bonus_only_for_preferred_role_at_good_cause_org():
    filters = FILTERS.model_copy(
        update={"good_cause_org_types": ["foundation_nonprofit", "government"], "good_cause_role_bonus": 10}
    )

    def bonus(**overrides) -> int:
        return score_vacancy(make(**overrides), PLACES, filters=filters).breakdown["good_cause_role"]

    assert bonus(role_type="policy_advice", org_type="government") == 10
    assert bonus(role_type="policy_advice", org_type="commercial_brand") == 0
    assert bonus(role_type="research", org_type="foundation_nonprofit") == 0


def test_rank_applies_filters():
    ranked = rank_vacancies([make("a", organisation="Red Bull"), make("b")], TODAY, PLACES, filters=FILTERS)
    assert [s.vacancy.title for s in ranked] == ["b"]


def test_real_job_filters_file_is_valid():
    filters = load_job_filters()
    assert "FIFA" in filters.excluded_organisations


def test_startup_and_app_penalties_add_up():
    both = score_vacancy(make(org_type="scaleup_tech", product_is_app=True), PLACES, filters=FILTERS)
    assert both.breakdown["startup_app_penalty"] == -20
    assert score_vacancy(make(org_type="foundation_nonprofit"), PLACES, filters=FILTERS).breakdown["startup_app_penalty"] == 0


def test_abroad_not_penalised_for_international_impact():
    intl = make(city="Nyon", country="CH", impact_scale="international")
    local = make(city="Nyon", country="CH", impact_scale="local")
    assert score(intl).breakdown["location"] == 10
    assert score(local).breakdown["location"] == 0


def test_impact_scale_points():
    points = {s: score(make(impact_scale=s)).breakdown["impact_scale"] for s in ("international", "national", "unknown", "local")}
    assert points == {"international": 20, "national": 12, "unknown": 5, "local": 0}
