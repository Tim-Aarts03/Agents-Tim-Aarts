from datetime import date

import pytest
from pydantic import ValidationError

from tools.applications_log import (
    Application,
    Status,
    add_proposed,
    known_urls,
    rate,
    read_log,
    update_status,
)

DAY = date(2026, 11, 20)
URL = "https://example.org/a"


def make_app(url: str = URL, score: int | None = 80) -> Application:
    return Application(
        url=url,
        organisation="Org",
        title="Job",
        status=Status.PROPOSED,
        date_proposed=DAY,
        date_updated=DAY,
        score=score,
        features="domain:sport_tech;org_type:government",
    )


def test_missing_log_is_empty(tmp_path):
    assert read_log(tmp_path / "applications.csv") == []


def test_add_and_read_roundtrip(tmp_path):
    path = tmp_path / "applications.csv"
    app = make_app(score=None)
    assert add_proposed(app, path) is True
    assert read_log(path) == [app]
    assert read_log(path)[0].feature_list() == ["domain:sport_tech", "org_type:government"]


def test_duplicate_url_is_not_added(tmp_path):
    path = tmp_path / "applications.csv"
    add_proposed(make_app(), path)
    assert add_proposed(make_app(), path) is False
    assert len(read_log(path)) == 1


def test_update_status_keeps_other_fields(tmp_path):
    path = tmp_path / "applications.csv"
    add_proposed(make_app(), path)
    later = date(2026, 11, 27)
    updated = update_status(URL, Status.SENT, later, path, letter_file="output/career/a.md", feedback="Kortere opening")
    assert updated.status is Status.SENT
    assert updated.date_updated == later
    assert updated.date_proposed == DAY
    assert updated.score == 80
    assert read_log(path)[0].feedback == "Kortere opening"
    assert known_urls(path) == {URL}


def test_rate_stores_rating_and_reason(tmp_path):
    path = tmp_path / "applications.csv"
    add_proposed(make_app(), path)
    rate(URL, 4, "Mooi netwerk", DAY, path)
    app = read_log(path)[0]
    assert (app.rating, app.rating_reason) == (4, "Mooi netwerk")


@pytest.mark.parametrize("bad", [0, 6])
def test_rating_must_be_1_to_5(tmp_path, bad):
    path = tmp_path / "applications.csv"
    add_proposed(make_app(), path)
    with pytest.raises(ValidationError):
        rate(URL, bad, "", DAY, path)


def test_old_log_format_without_new_columns_still_reads(tmp_path):
    path = tmp_path / "applications.csv"
    path.write_text(
        "url,organisation,title,status,date_proposed,date_updated,score,letter_file,feedback\n"
        f"{URL},Org,Job,proposed,2026-11-20,2026-11-20,,,\n",
        encoding="utf-8",
    )
    app = read_log(path)[0]
    assert app.rating is None and app.score is None and app.features == ""


def test_update_unknown_url_raises(tmp_path):
    with pytest.raises(KeyError):
        update_status("https://nope.org", Status.SENT, DAY, tmp_path / "applications.csv")


def test_training_status_roundtrip(tmp_path):
    path = tmp_path / "applications.csv"
    app = make_app("https://training.invalid/v01").model_copy(update={"status": Status.TRAINING})
    add_proposed(app, path)
    assert read_log(path)[0].status is Status.TRAINING
