from datetime import date

import pytest

from tools.applications_log import Application, Status, add_proposed, known_urls, read_log, update_status

DAY = date(2026, 11, 20)


def make_app(url: str = "https://example.org/a", score: int | None = 80) -> Application:
    return Application(
        url=url,
        organisation="Org",
        title="Job",
        status=Status.PROPOSED,
        date_proposed=DAY,
        date_updated=DAY,
        score=score,
    )


def test_missing_log_is_empty(tmp_path):
    assert read_log(tmp_path / "applications.csv") == []


def test_add_and_read_roundtrip(tmp_path):
    path = tmp_path / "applications.csv"
    app = make_app(score=None)
    assert add_proposed(app, path) is True
    assert read_log(path) == [app]


def test_duplicate_url_is_not_added(tmp_path):
    path = tmp_path / "applications.csv"
    add_proposed(make_app(), path)
    assert add_proposed(make_app(), path) is False
    assert len(read_log(path)) == 1


def test_update_status_keeps_other_fields(tmp_path):
    path = tmp_path / "applications.csv"
    add_proposed(make_app(), path)
    later = date(2026, 11, 27)
    updated = update_status(
        "https://example.org/a", Status.SENT, later, path, letter_file="output/career/a.md", feedback="Kortere opening"
    )
    assert updated.status is Status.SENT
    assert updated.date_updated == later
    assert updated.date_proposed == DAY
    assert read_log(path)[0].feedback == "Kortere opening"
    assert known_urls(path) == {"https://example.org/a"}


def test_update_unknown_url_raises(tmp_path):
    with pytest.raises(KeyError):
        update_status("https://nope.org", Status.SENT, DAY, tmp_path / "applications.csv")
