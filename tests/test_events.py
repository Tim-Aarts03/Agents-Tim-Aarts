from datetime import date, timedelta

import pytest

from tools.events import (
    DEFAULT_WINDOW_DAYS,
    MAX_LEARNED_BONUS,
    MIN_RATINGS,
    Audience,
    Event,
    LoggedEvent,
    Location,
    NetworkEvidence,
    PriceBand,
    Status,
    Topic,
    add_proposed,
    classify_location,
    event_features,
    feature_bonuses,
    month_status,
    price_band,
    rank_events,
    read_log,
    score_event,
    update_event,
)
from tools.job_scoring import JobFilters

TODAY = date(2026, 11, 20)
PLACES = {"haarlem", "amsterdam", "heemstede"}


def event(**overrides) -> Event:
    data = {
        "title": "Sport & Society Night",
        "organiser": "Kenniscentrum Sport & Bewegen",
        "url": "https://example.org/e1",
        "start_date": TODAY + timedelta(days=10),
        "city": "Amsterdam",
    }
    data.update(overrides)
    return Event.model_validate(data)


def logged(features: str, rating: int | None, n: int = 0, **overrides) -> LoggedEvent:
    data = {
        "url": f"https://example.org/{n}", "organiser": "Org", "title": "Event", "event_date": TODAY,
        "status": Status.PROPOSED, "date_proposed": TODAY, "date_updated": TODAY,
        "rating": rating, "features": features,
    }
    data.update(overrides)
    return LoggedEvent.model_validate(data)


@pytest.mark.parametrize(("price", "band"), [
    (None, PriceBand.UNKNOWN), (0, PriceBand.FREE), (49.99, PriceBand.UNDER_50),
    (50, PriceBand.FROM_50_TO_150), (150, PriceBand.FROM_50_TO_150), (150.01, PriceBand.OVER_150),
])
def test_price_band(price, band):
    assert price_band(price) is band


@pytest.mark.parametrize(("overrides", "location"), [
    ({"city": "Haarlem"}, Location.PREFERRED_REGION),
    ({"city": " amsterdam "}, Location.PREFERRED_REGION),
    ({"city": "Utrecht"}, Location.OTHER_NETHERLANDS),
    ({"city": "Nyon", "country": "CH"}, Location.ABROAD),
    ({"city": None}, Location.UNKNOWN),
    ({"city": "Amsterdam", "online": True}, Location.ONLINE),
])
def test_classify_location(overrides, location):
    assert classify_location(event(**overrides), PLACES) is location


def test_no_price_filter_expensive_event_still_ranked():
    ranked = rank_events([event(price_eur=495)], TODAY, PLACES)
    assert len(ranked) == 1 and ranked[0].price_band is PriceBand.OVER_150


def test_window_and_deadline_exclusions():
    events = [
        event(url="https://example.org/past", start_date=TODAY - timedelta(days=1)),
        event(url="https://example.org/today", start_date=TODAY),
        event(url="https://example.org/edge", start_date=TODAY + timedelta(days=DEFAULT_WINDOW_DAYS)),
        event(url="https://example.org/far", start_date=TODAY + timedelta(days=DEFAULT_WINDOW_DAYS + 1)),
        event(url="https://example.org/closed", registration_deadline=TODAY - timedelta(days=1)),
        event(url="https://example.org/full", sold_out=True),
        event(url="https://example.org/online", online=True),
    ]
    urls = {str(s.event.url) for s in rank_events(events, TODAY, PLACES)}
    assert urls == {"https://example.org/today", "https://example.org/edge"}


def test_excluded_organiser_and_known_urls_skipped():
    events = [
        event(url="https://example.org/fifa", organiser="FIFA Foundation"),
        event(url="https://example.org/known"),
        event(url="https://example.org/new"),
        event(url="https://example.org/new"),  # duplicate
    ]
    ranked = rank_events(events, TODAY, PLACES, exclude_urls={"https://example.org/known"},
                         filters=JobFilters(excluded_organisations=["FIFA"]))
    assert [str(s.event.url) for s in ranked] == ["https://example.org/new"]


def test_network_evidence_capped():
    scored = score_event(event(network_evidence=list(NetworkEvidence)), PLACES)
    assert scored.breakdown["network"] == 20


def test_extra_topics_add_small_bonus():
    one = score_event(event(topics=[Topic.SPORT_POLICY]), PLACES).breakdown["topic"]
    two = score_event(event(topics=[Topic.SPORT_POLICY, Topic.SPORT_TECH]), PLACES).breakdown["topic"]
    assert (one, two) == (12, 15)


def test_features_skip_unknowns():
    features = event_features(event(city=None, topics=[Topic.SPORT_POLICY]), PLACES)
    assert features == ["topic:sport_policy"]


def test_features_include_location_and_price():
    features = event_features(event(audience=Audience.MIXED, price_eur=0), PLACES)
    assert "location:preferred_region" in features and "price:free" in features and "audience:mixed" in features


def test_learning_needs_minimum_ratings_and_prefers_after_rating():
    few = [logged("price:free", 5, i) for i in range(MIN_RATINGS - 1)]
    assert feature_bonuses(few) == {}
    # Looked great beforehand (5), was disappointing in reality (1): reality wins.
    apps = [logged("event_type:conference", 5, i, after_rating=1) for i in range(MIN_RATINGS)]
    assert feature_bonuses(apps)["event_type:conference"] < 0


def test_learned_bonus_changes_ranking_and_is_capped():
    bonuses = {"topic:sport_tech": 100.0}
    tech = event(url="https://example.org/tech", topics=[Topic.SPORT_TECH])
    policy = event(url="https://example.org/policy", topics=[Topic.SPORT_POLICY])
    ranked = rank_events([policy, tech], TODAY, PLACES, bonuses=bonuses)
    assert str(ranked[0].event.url) == "https://example.org/tech"
    assert ranked[0].breakdown["learned_from_ratings"] == MAX_LEARNED_BONUS


def test_month_status():
    events = [
        logged("", None, 1, status=Status.ATTENDED, event_date=date(2026, 11, 5)),
        logged("", None, 2, status=Status.REGISTERED, event_date=date(2026, 12, 10)),
        logged("", None, 3, status=Status.PROPOSED, event_date=date(2026, 12, 1)),
    ]
    status = month_status(events, TODAY)
    assert status["done_this_month"] is True and len(status["upcoming"]) == 1
    assert month_status(events, date(2026, 12, 1))["done_this_month"] is True
    assert month_status(events, date(2027, 1, 2))["done_this_month"] is False


def test_log_roundtrip_and_update(tmp_path):
    path = tmp_path / "events.csv"
    assert add_proposed(logged("topic:sport_policy", None, 1, price_eur=25.0), path)
    assert not add_proposed(logged("", None, 1), path)
    update_event("https://example.org/1", TODAY, path, rating=4, rating_reason="goed netwerk")
    [e] = read_log(path)
    assert (e.rating, e.price_eur, e.feature_list()) == (4, 25.0, ["topic:sport_policy"])
    with pytest.raises(KeyError):
        update_event("https://example.org/missing", TODAY, path, rating=1)


def test_small_group_earns_no_network_points():
    assert score_event(event(network_evidence=[NetworkEvidence.SMALL_GROUP]), PLACES).breakdown["network"] == 0
