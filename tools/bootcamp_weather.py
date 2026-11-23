"""Weather advice for the Tuesday bootcamp (free Open-Meteo API, no key needed)."""

from __future__ import annotations

import json
import urllib.request
from datetime import date

from pydantic import BaseModel

# Hof van Jacob, Haarlem (approximate; city-level accuracy is enough for a forecast).
LATITUDE = 52.38
LONGITUDE = 4.64
SESSION_HOURS = (16, 17)  # 16:15–17:00 local time
COLD_BELOW_C = 12.0
RAIN_PROBABILITY_PERCENT = 50
FORECAST_URL = (
    "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,precipitation_probability&timezone=Europe%2FAmsterdam"
    "&start_date={day}&end_date={day}"
)


class SessionForecast(BaseModel):
    min_temperature_c: float
    max_rain_probability: int


class WeatherAdvice(BaseModel):
    lines: list[str]
    forecast_available: bool


def parse_forecast(payload: dict) -> SessionForecast:
    hourly = payload["hourly"]
    rows = [
        (temp, rain)
        for t, temp, rain in zip(hourly["time"], hourly["temperature_2m"], hourly["precipitation_probability"])
        if int(t[11:13]) in SESSION_HOURS
    ]
    if not rows:
        raise ValueError("forecast has no data for the session hours")
    return SessionForecast(
        min_temperature_c=min(r[0] for r in rows),
        max_rain_probability=max(r[1] or 0 for r in rows),
    )


def fetch_session_forecast(session_date: date, timeout: float = 10.0) -> SessionForecast | None:
    """Returns None when the forecast cannot be fetched; the reminder then goes out without weather advice."""
    url = FORECAST_URL.format(lat=LATITUDE, lon=LONGITUDE, day=session_date.isoformat())
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return parse_forecast(json.load(response))
    except (OSError, ValueError, KeyError):
        return None


def advice_for_session(forecast: SessionForecast | None) -> WeatherAdvice:
    if forecast is None:
        return WeatherAdvice(lines=[], forecast_available=False)
    lines = []
    if forecast.min_temperature_c < COLD_BELOW_C:
        lines.append("Het wordt fris, dus trek warme kleding aan.")
    if forecast.max_rain_probability >= RAIN_PROBABILITY_PERCENT:
        lines.append("We staan op het overdekte balkon van team 2, dus regen is geen probleem.")
    return WeatherAdvice(lines=lines, forecast_available=True)
