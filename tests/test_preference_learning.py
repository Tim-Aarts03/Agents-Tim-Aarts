from datetime import date

import pytest

from tools.applications_log import Application, Status
from tools.preference_learning import MIN_RATINGS, feature_bonuses, summary

DAY = date(2026, 11, 20)


def rated(features: str, rating: int | None, n: int = 0) -> Application:
    return Application(
        url=f"https://example.org/{n}",
        organisation="Org",
        title="Job",
        status=Status.PROPOSED,
        date_proposed=DAY,
        date_updated=DAY,
        rating=rating,
        features=features,
    )


def test_feature_needs_minimum_ratings():
    apps = [rated("org_type:government", 5, i) for i in range(MIN_RATINGS - 1)]
    assert feature_bonuses(apps) == {}


@pytest.mark.parametrize(("ratings", "bonus"), [([5, 5, 5], 5.0), ([1, 1, 1], -5.0), ([3, 3, 3], 0.0), ([2, 3, 4], 0.0)])
def test_bonus_scales_with_average_rating(ratings, bonus):
    apps = [rated("role_type:research", r, i) for i, r in enumerate(ratings)]
    assert feature_bonuses(apps) == {"role_type:research": pytest.approx(bonus)}


def test_unrated_applications_are_ignored():
    apps = [rated("org_type:government", None, i) for i in range(5)]
    assert feature_bonuses(apps) == {}


def test_each_feature_learned_separately():
    apps = [rated("org_type:commercial_brand;role_type:commercial_sales", 2, i) for i in range(3)]
    apps += [rated("org_type:commercial_brand;role_type:marketing_communication", 5, i + 10) for i in range(3)]
    bonuses = feature_bonuses(apps)
    assert bonuses["role_type:commercial_sales"] == pytest.approx(-2.5)
    assert bonuses["role_type:marketing_communication"] == pytest.approx(5.0)
    assert bonuses["org_type:commercial_brand"] == pytest.approx(1.25)  # avg 3.5


def test_summary_lists_strongest_signal_first():
    apps = [rated("org_type:government", 3, 0), rated("domain:sport_tech", 1, 1)]
    lines = summary(apps)
    assert lines[0].startswith("domain:sport_tech: gemiddeld 1.0")
    assert "nog 2 beoordeling(en) nodig" in lines[0]


def test_org_features_learn_from_org_rating():
    apps = [rated("org_type:commercial_brand;impact_scale:international;role_type:marketing_communication", 1, i)
            for i in range(3)]
    for app in apps:
        app.org_rating = 5
    bonuses = feature_bonuses(apps)
    assert bonuses["org_type:commercial_brand"] == pytest.approx(5.0)
    assert bonuses["impact_scale:international"] == pytest.approx(5.0)
    assert bonuses["role_type:marketing_communication"] == pytest.approx(-5.0)


def test_org_features_fall_back_to_role_rating():
    apps = [rated("org_type:government", 4, i) for i in range(3)]
    assert feature_bonuses(apps) == {"org_type:government": pytest.approx(2.5)}


def test_org_rating_alone_only_teaches_org_features():
    apps = [rated("org_type:government;role_type:policy", None, i) for i in range(3)]
    for app in apps:
        app.org_rating = 5
    assert feature_bonuses(apps) == {"org_type:government": pytest.approx(5.0)}
