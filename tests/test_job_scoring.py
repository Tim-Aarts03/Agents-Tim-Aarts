from datetime import date

import pytest
from pydantic import ValidationError

from tools.job_scoring import Domain, Hours, Location, Vacancy, is_expired, rank_vacancies, score_vacancy

TODAY = date(2026, 11, 20)


def make(title: str = "Job", **overrides) -> Vacancy:
    data = {
        "title": title,
        "organisation": "Org",
        "url": f"https://example.org/{title.replace(' ', '-')}",
        "location": Location.PREFERRED_REGION,
    }
    data.update(overrides)
    return Vacancy(**data)


def test_best_single_domain_vacancy_scores_95():
    v = make(
        domains=[Domain.SPORT_FOR_VULNERABLE_GROUPS],
        strong_learning_environment=True,
        hours=Hours.PART_TIME,
    )
    result = score_vacancy(v)
    assert result.score == 95
    assert result.breakdown == {
        "domain": 40,
        "learning_environment": 25,
        "location": 20,
        "hours": 10,
        "requirements_risk": 0,
    }


def test_second_domain_adds_bonus_and_score_is_capped():
    v = make(
        domains=[Domain.SPORT_TECH, Domain.SPORT_FOR_VULNERABLE_GROUPS],
        strong_learning_environment=True,
        hours=Hours.PART_TIME,
    )
    assert score_vacancy(v).breakdown["domain"] == 45
    assert score_vacancy(v).score == 100


def test_duplicate_domains_do_not_count_twice():
    v = make(domains=[Domain.SPORT_TECH, Domain.SPORT_TECH])
    assert score_vacancy(v).breakdown["domain"] == 30


def test_no_matching_domain_and_abroad_scores_low():
    v = make(location=Location.ABROAD, hours=Hours.FULL_TIME)
    assert score_vacancy(v).score == 5


def test_requirements_risk_penalty_never_below_zero():
    v = make(location=Location.ABROAD, hours=Hours.FULL_TIME, requirements_risk=True)
    assert score_vacancy(v).score == 0


@pytest.mark.parametrize(
    ("deadline", "expired"),
    [(None, False), (date(2026, 11, 19), True), (TODAY, False), (date(2026, 11, 21), False)],
)
def test_deadline_boundaries(deadline, expired):
    assert is_expired(make(deadline=deadline), TODAY) is expired


def test_rank_drops_expired_and_duplicates_and_limits_to_top_n():
    vacancies = [make(f"job {i}", domains=[Domain.SPORT_TECH]) for i in range(8)]
    vacancies.append(make("old", domains=[Domain.SPORT_FOR_VULNERABLE_GROUPS], deadline=date(2026, 1, 1)))
    vacancies.append(make("job 0", domains=[Domain.SPORT_FOR_VULNERABLE_GROUPS]))  # duplicate URL
    ranked = rank_vacancies(vacancies, TODAY)
    titles = [s.vacancy.title for s in ranked]
    assert len(ranked) == 5
    assert "old" not in titles
    assert titles.count("job 0") == 1


def test_rank_orders_by_score_then_earliest_deadline():
    best = make("best", domains=[Domain.SPORT_FOR_VULNERABLE_GROUPS])
    tie_late = make("tie late", domains=[Domain.SPORT_TECH], deadline=date(2026, 12, 31))
    tie_early = make("tie early", domains=[Domain.SPORT_TECH], deadline=date(2026, 12, 1))
    ranked = rank_vacancies([tie_late, tie_early, best], TODAY)
    assert [s.vacancy.title for s in ranked] == ["best", "tie early", "tie late"]


def test_invalid_input_is_rejected():
    with pytest.raises(ValidationError):
        make(url="not a url")
    with pytest.raises(ValidationError):
        make(domains=["football_betting"])
