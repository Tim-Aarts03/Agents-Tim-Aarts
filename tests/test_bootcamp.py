from datetime import date
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from tools.bootcamp_mail import Group, Pitch, dutch_date, log_mail, next_tuesday, promo_mail, read_mail_log, reminder_mail
from tools.bootcamp_weather import SessionForecast, advice_for_session, fetch_session_forecast, parse_forecast

PITCH = Pitch(text="Koppel jezelf los na een lange werkdag. Doe gratis mee!")
LINK = "https://forms.gle/example"


@pytest.mark.parametrize(
    ("sent", "session"),
    [
        (date(2026, 11, 18), date(2026, 11, 24)),  # Wednesday -> next Tuesday
        (date(2026, 11, 23), date(2026, 11, 24)),  # Monday -> tomorrow
        (date(2026, 11, 24), date(2026, 12, 1)),  # Tuesday -> next week
        (date(2026, 12, 30), date(2027, 1, 5)),  # across new year
    ],
)
def test_next_tuesday(sent, session):
    assert next_tuesday(sent) == session


def test_dutch_date():
    assert dutch_date(date(2026, 12, 1)) == "1 december"


def test_promo_mail_hof_van_jacob():
    mail = promo_mail(Group.HOF_VAN_JACOB, PITCH, LINK, date(2026, 11, 25), ["mama@example.org"])
    assert mail.to == ["mama@example.org"]
    assert mail.subject == "Beweegsessie dinsdag 1 december – meld je aan"
    assert mail.body.startswith("Beste collega's,\n\nKoppel jezelf los")
    assert "Dinsdag 1 december om 16:15 is er een nieuwe beweegsessie. Meld je aan via de onderstaande link:" in mail.body
    assert LINK in mail.body
    assert mail.body.endswith("Met vriendelijke groet,\nTim Aarts")


def test_promo_mail_greeting_jacob_kliniek():
    mail = promo_mail(Group.JACOB_KLINIEK, PITCH, LINK, date(2026, 11, 25), [])
    assert mail.body.startswith("Goedemiddag team Jacob Kliniek,")


@pytest.mark.parametrize("bad", ["Te kort", "Een. Twee. Drie. Vier."])
def test_pitch_validation(bad):
    with pytest.raises(ValidationError):
        Pitch(text=bad)


def test_reminder_without_forecast_is_standard_text():
    mail = reminder_mail(date(2026, 11, 24), advice_for_session(None), ["a@example.org"])
    assert mail.subject == "Reminder: beweegsessie morgen (24 november) om 16:15"
    assert mail.body == (
        "!Reminder!\n\nWat leuk dat jij je hebt aangemeld voor de beweegsessie van morgen.\n"
        "Vergeet je sportspullen niet mee te nemen.\n\nTot morgen!\n\nMet vriendelijke groet,\nTim Aarts"
    )


@pytest.mark.parametrize(
    ("temp", "rain", "cold", "balcony"),
    [(11.9, 10, True, False), (12.0, 10, False, False), (15, 50, False, True), (5, 80, True, True), (15, 49, False, False)],
)
def test_weather_advice_boundaries(temp, rain, cold, balcony):
    lines = advice_for_session(SessionForecast(min_temperature_c=temp, max_rain_probability=rain)).lines
    assert any("warme kleding" in line for line in lines) is cold
    assert any("balkon van team 2" in line for line in lines) is balcony


def test_reminder_includes_weather_lines():
    advice = advice_for_session(SessionForecast(min_temperature_c=6, max_rain_probability=70))
    body = reminder_mail(date(2026, 11, 24), advice, []).body
    assert "warme kleding" in body and "balkon van team 2" in body
    assert body.index("sportspullen") < body.index("warme kleding") < body.index("Tot morgen!")


def test_parse_forecast_uses_only_session_hours():
    payload = {
        "hourly": {
            "time": ["2026-11-24T15:00", "2026-11-24T16:00", "2026-11-24T17:00", "2026-11-24T18:00"],
            "temperature_2m": [3.0, 9.5, 8.0, 1.0],
            "precipitation_probability": [90, 20, None, 95],
        }
    }
    assert parse_forecast(payload) == SessionForecast(min_temperature_c=8.0, max_rain_probability=20)


def test_fetch_returns_none_when_offline():
    with patch("urllib.request.urlopen", side_effect=OSError("no network")):
        assert fetch_session_forecast(date(2026, 11, 24)) is None


def test_mail_log_roundtrip(tmp_path):
    path = tmp_path / "bootcamp_mails.csv"
    log_mail(date(2026, 11, 25), "promo", "hof_van_jacob", PITCH.text, path)
    log_mail(date(2026, 11, 30), "reminder", "registered", "", path)
    rows = read_mail_log(path)
    assert [r["session_date"] for r in rows] == ["2026-12-01", "2026-12-01"]
    assert rows[0]["pitch"] == PITCH.text
