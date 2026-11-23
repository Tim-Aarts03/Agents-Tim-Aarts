import json
from pathlib import Path

import pytest

from tools import crypto
from tools.crypto import HOUR_MS, Config, Rule

T0 = 1_700_000_000_000 // HOUR_MS * HOUR_MS
FAST = Rule(name="sma_cross_2_4", kind="sma_cross", fast=2, slow=4)


def cfg(**kw) -> Config:
    base = dict(pairs=["BTCEUR"], start_eur=100.0, fee_rate=0.0, divergence_pp=5.0, stale_hours=24,
                active=FAST, history=[])
    base.update(kw)
    return Config(**base)


def fake_api(prices: list[float], start: int = T0):
    """Public-API stand-in: hourly candles from `start`, never hits the network."""
    calls = []

    def fetch(url: str) -> list:
        calls.append(url)
        q = dict(p.split("=") for p in url.split("?")[1].split("&"))
        begin = int(q["startTime"])
        rows = [[start + i * HOUR_MS, "0", "0", "0", str(p)] for i, p in enumerate(prices)
                if start + i * HOUR_MS >= begin]
        return rows[: int(q["limit"])]
    fetch.calls = calls
    return fetch


def paths(tmp_path: Path) -> dict:
    return dict(state_file=tmp_path / "s.json", trades_file=tmp_path / "t.csv", equity_file=tmp_path / "e.csv")


def test_only_public_price_api_is_allowed():
    with pytest.raises(ValueError):
        crypto.http_get("https://api.binance.com/api/v3/order?symbol=BTCEUR")
    with pytest.raises(ValueError):
        crypto.http_get("https://example.com/api/v3/klines?x=1")


def test_open_candle_is_ignored():
    prices = [1.0, 2.0, 3.0]
    now = T0 + 2 * HOUR_MS + 10  # third candle still open
    assert crypto.fetch_closes("BTCEUR", T0, now, fake_api(prices)) == [(T0, 1.0), (T0 + HOUR_MS, 2.0)]


def test_sma_cross_signals():
    sig = crypto.signals([10, 10, 10, 10, 20, 5, 5, 5], FAST)
    assert sig[:3] == [None, None, None]
    assert sig[4] is True and sig[7] is False


def test_breakout_signals():
    rule = Rule(name="b", kind="breakout", fast=2, slow=3)
    sig = crypto.signals([5, 5, 5, 6, 7, 4, 4], rule)
    assert sig[3] is True and sig[5] is False


def test_simulate_applies_fee_both_ways():
    value, trades = crypto.simulate([10, 20], [True, False], 0, 2, 100.0, 0.01)
    assert trades == 2
    assert value == pytest.approx(100 * 0.99 / 10 * 20 * 0.99)


def test_tick_buys_and_sells_paper_only(tmp_path):
    p = paths(tmp_path)
    prices = [10, 10, 10, 10, 20]
    now = T0 + len(prices) * HOUR_MS
    trades = crypto.tick(now, cfg(), fake_api(prices), **p)
    assert [t["side"] for t in trades] == ["buy"]
    prices += [5, 5]
    trades = crypto.tick(T0 + len(prices) * HOUR_MS, cfg(), fake_api(prices), **p)
    assert [t["side"] for t in trades] == ["sell"]
    state = json.loads(p["state_file"].read_text())
    assert state["pairs"]["BTCEUR"]["units"] == 0
    assert state["pairs"]["BTCEUR"]["cash"] == pytest.approx(100 / 20 * 5)
    eq = crypto.read_csv(p["equity_file"])
    assert eq[-1]["missed_hours"] == "1"  # one candle skipped while "asleep"


def test_tick_without_new_candle_books_nothing(tmp_path):
    p = paths(tmp_path)
    prices = [10, 10, 10, 10, 20]
    now = T0 + 5 * HOUR_MS
    crypto.tick(now, cfg(), fake_api(prices), **p)
    assert crypto.tick(now + 60_000, cfg(), fake_api(prices), **p) == []
    assert len(crypto.read_csv(p["trades_file"])) == 1


def test_tick_alerts_only_after_stale_hours(tmp_path):
    p = paths(tmp_path)
    crypto.tick(T0 + 5 * HOUR_MS, cfg(), fake_api([10] * 5), **p)
    alerts = []

    def broken(url):
        raise OSError("offline")

    with pytest.raises(OSError):
        crypto.tick(T0 + 10 * HOUR_MS, cfg(), broken, alert=alerts.append, **p)
    assert alerts == []
    with pytest.raises(OSError):
        crypto.tick(T0 + 40 * HOUR_MS, cfg(), broken, alert=alerts.append, **p)
    with pytest.raises(OSError):
        crypto.tick(T0 + 41 * HOUR_MS, cfg(), broken, alert=alerts.append, **p)
    assert len(alerts) == 1  # max one alert per day
    assert "offline" in json.loads(p["state_file"].read_text())["last_error"]


def test_report_compares_pot_with_market_and_flags(tmp_path):
    p = paths(tmp_path)
    prices = [10, 10, 10, 10, 20]
    crypto.tick(T0 + 5 * HOUR_MS, cfg(), fake_api(prices), **p)
    prices += [40]
    crypto.tick(T0 + 6 * HOUR_MS, cfg(), fake_api(prices), **p)
    r = crypto.report(T0 + 6 * HOUR_MS, 7, cfg(), **p)
    assert r["week"]["pot_pct"] == pytest.approx(100.0)
    assert r["week"]["market_pct"] == pytest.approx(100.0)
    assert r["flag_divergence"] is False
    assert len(r["trades"]) == 1


def test_report_without_data(tmp_path):
    r = crypto.report(T0, 7, cfg(), **paths(tmp_path))
    assert r["note"].startswith("no market-watch data")


def test_backtest_judges_on_unseen_part():
    up = [float(i) for i in range(1, 201)]
    res = crypto.backtest({"X": up}, [FAST], fee=0.0, split=0.5)
    assert res["buy_hold"]["test_pct"] == pytest.approx((200 / 101 - 1) * 100, abs=0.01)
    assert res["best_on_train"]["rule"] == FAST.name
    assert "coin_flip_test_median_pct" in res


def test_activate_needs_approval(tmp_path):
    f = tmp_path / "rules.json"
    f.write_text(json.dumps({"active": FAST.model_dump(), "history": []}))
    with pytest.raises(PermissionError):
        crypto.activate("breakout_24_336", False, "x", "2026-11-23", f)
    with pytest.raises(ValueError):
        crypto.activate("made_up", True, "x", "2026-11-23", f)
    crypto.activate("breakout_24_336", True, "better on test", "2026-11-23", f)
    data = json.loads(f.read_text())
    assert data["active"]["name"] == "breakout_24_336" and data["history"][0]["approved_by"] == "Tim"


def test_real_config_is_valid():
    c = crypto.load_config()
    assert c.active.name in {r.name for r in crypto.candidate_rules()}
    assert c.start_eur == 100.0


def test_plist_runs_tick_hourly_in_project():
    text = crypto.plist_text(Path("/p"), Path("/p/.venv/bin/python"))
    assert "<integer>3600</integer>" in text and "<string>tick</string>" in text
    assert "<string>/p</string>" in text
