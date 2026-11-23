"""Paper-trading market watch for BTC/ETH. Never real money, never an exchange account.

`tick` runs every hour (macOS launchd): it fetches closed 1h candles from
Binance's public price API, applies the active rule and books paper trades in
a virtual pot. `report` feeds the Thursday analysis; `backtest` lets the
analyst test candidate rules on data they were not tuned on. The active rule
only changes through `activate --approved` (Tim's approval).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import subprocess
import sys
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Callable, Literal

from pydantic import BaseModel

CONFIG_FILE = Path("knowledge/crypto_rules.json")
LOG_DIR = Path("logs")
STATE_FILE = LOG_DIR / "crypto_state.json"
TRADES_FILE = LOG_DIR / "crypto_paper_trades.csv"
EQUITY_FILE = LOG_DIR / "crypto_equity.csv"
HOUR_MS = 3_600_000
# The only host this tool may call: public market data, no account, no keys.
API = "https://api.binance.com/api/v3/klines"
LAUNCHD_LABEL = "com.agents.crypto-watch"

TRADE_FIELDS = ["ts_utc", "pair", "side", "price", "units", "eur", "fee", "rule", "pot_eur"]
EQUITY_FIELDS = ["ts_utc", "candle_ms", "pot_eur", "closes", "missed_hours"]

Fetch = Callable[[str], list]


class Rule(BaseModel):
    name: str
    kind: Literal["sma_cross", "breakout"]
    fast: int  # hours
    slow: int  # hours

    @property
    def warmup(self) -> int:
        return self.slow + self.fast + 48


class Config(BaseModel):
    pairs: list[str]
    start_eur: float
    fee_rate: float
    divergence_pp: float
    stale_hours: float
    active: Rule
    history: list[dict]


class PairState(BaseModel):
    cash: float
    units: float = 0.0
    last_ms: int | None = None


class State(BaseModel):
    pairs: dict[str, PairState]
    last_ok: str | None = None
    last_error: str | None = None
    last_alert: str | None = None


# ---------- data ----------

def http_get(url: str) -> list:
    if not url.startswith(API + "?"):
        raise ValueError(f"refusing to call {url}: only public price data is allowed")
    req = urllib.request.Request(url, headers={"User-Agent": "paper-market-watch"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def fetch_closes(pair: str, start_ms: int, now_ms: int, fetch: Fetch = http_get) -> list[tuple[int, float]]:
    """Closed 1h candles from start_ms up to now: [(open_ms, close)]."""
    out: list[tuple[int, float]] = []
    cursor = start_ms
    while cursor < now_ms:
        rows = fetch(f"{API}?symbol={pair}&interval=1h&startTime={cursor}&limit=1000")
        if not rows:
            break
        for r in rows:
            open_ms = int(r[0])
            if open_ms + HOUR_MS <= now_ms and (not out or open_ms > out[-1][0]):
                out.append((open_ms, float(r[4])))
        nxt = int(rows[-1][0]) + HOUR_MS
        if nxt <= cursor or len(rows) < 1000:
            break
        cursor = nxt
    return out


# ---------- rules ----------

def signals(closes: list[float], rule: Rule) -> list[bool | None]:
    """Desired position (in market or not) after each close; None during warm-up."""
    n = len(closes)
    out: list[bool | None] = [None] * n
    if rule.kind == "sma_cross":
        prefix = [0.0]
        for c in closes:
            prefix.append(prefix[-1] + c)
        for i in range(rule.slow - 1, n):
            fast = (prefix[i + 1] - prefix[i + 1 - rule.fast]) / rule.fast
            slow = (prefix[i + 1] - prefix[i + 1 - rule.slow]) / rule.slow
            out[i] = fast > slow
    else:  # breakout: enter above the slow-window high, leave below the fast-window low
        holding = False
        for i in range(rule.slow, n):
            if not holding and closes[i] > max(closes[i - rule.slow:i]):
                holding = True
            elif holding and closes[i] < min(closes[i - rule.fast:i]):
                holding = False
            out[i] = holding
    return out


def candidate_rules() -> list[Rule]:
    rules = [Rule(name=f"sma_cross_{f}_{s}", kind="sma_cross", fast=f, slow=s)
             for f in (6, 12, 24, 48) for s in (72, 168, 336)]
    rules += [Rule(name=f"breakout_{f}_{s}", kind="breakout", fast=f, slow=s)
              for f in (24, 48, 72) for s in (72, 168, 336) if f < s]
    return rules


def simulate(closes: list[float], desired: list[bool | None], start: int, end: int,
             cash: float, fee: float) -> tuple[float, int]:
    """Paper result of following `desired` on closes[start:end]: (final value, trades)."""
    units, trades = 0.0, 0
    for i in range(start, end):
        want = desired[i]
        if want is None:
            continue
        if want and units == 0 and cash > 0:
            units, cash, trades = cash * (1 - fee) / closes[i], 0.0, trades + 1
        elif not want and units > 0:
            cash, units, trades = units * closes[i] * (1 - fee), 0.0, trades + 1
    return cash + units * closes[end - 1], trades


# ---------- config / state / logs ----------

def load_config(path: Path = CONFIG_FILE) -> Config:
    return Config.model_validate_json(path.read_text(encoding="utf-8"))


def load_state(cfg: Config, path: Path = STATE_FILE) -> State:
    if path.exists():
        return State.model_validate_json(path.read_text(encoding="utf-8"))
    share = cfg.start_eur / len(cfg.pairs)
    return State(pairs={p: PairState(cash=share) for p in cfg.pairs})


def save_state(state: State, path: Path = STATE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")


def append_csv(path: Path, fields: list[str], row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerow(row)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, UTC).isoformat(timespec="minutes")


def notify(message: str) -> None:
    # Only for failures (Tim does not want a ping per paper trade).
    subprocess.run(["osascript", "-e", f'display notification "{message}" with title "Crypto-marktwacht"'],
                   check=False)


# ---------- hourly tick ----------

def tick(now_ms: int, cfg: Config | None = None, fetch: Fetch = http_get,
         state_file: Path = STATE_FILE, trades_file: Path = TRADES_FILE, equity_file: Path = EQUITY_FILE,
         alert: Callable[[str], None] = notify) -> list[dict]:
    """One market-watch step. After sleep/downtime it acts on the latest signal only,
    at the current price: a real person could not have traded the missed hours."""
    cfg = cfg or load_config()
    state = load_state(cfg, state_file)
    rule = cfg.active
    trades: list[dict] = []
    try:
        data = {p: fetch_closes(p, now_ms - rule.warmup * HOUR_MS, now_ms, fetch) for p in cfg.pairs}
    except Exception as exc:  # network down, API change: record, alert when it lasts
        state.last_error = f"{iso(now_ms)} {type(exc).__name__}: {exc}"
        last_ok = datetime.fromisoformat(state.last_ok) if state.last_ok else None
        now = datetime.fromtimestamp(now_ms / 1000, UTC)
        last_alert = datetime.fromisoformat(state.last_alert) if state.last_alert else None
        if last_ok and now - last_ok > timedelta(hours=cfg.stale_hours) and (
                not last_alert or now - last_alert > timedelta(hours=24)):
            alert(f"Al {int((now - last_ok).total_seconds() // 3600)} uur geen koersen. Vraag Max om te kijken.")
            state.last_alert = now.isoformat(timespec="minutes")
        save_state(state, state_file)
        raise

    latest = {p: data[p][-1] for p in cfg.pairs if data[p]}
    missed = 0
    for pair, (ms, price) in latest.items():
        ps = state.pairs.setdefault(pair, PairState(cash=0.0))
        if ps.last_ms is not None and ms <= ps.last_ms:
            continue
        if ps.last_ms is not None:
            missed = max(missed, (ms - ps.last_ms) // HOUR_MS - 1)
        want = signals([c for _, c in data[pair]], rule)[-1]
        side = None
        if want and ps.units == 0 and ps.cash > 0:
            fee = ps.cash * cfg.fee_rate
            ps.units, eur, ps.cash, side = (ps.cash - fee) / price, ps.cash, 0.0, "buy"
        elif want is False and ps.units > 0:
            eur = ps.units * price
            fee = eur * cfg.fee_rate
            units, ps.cash, ps.units, side = ps.units, eur - fee, 0.0, "sell"
        if side:
            trades.append({"ts_utc": iso(ms + HOUR_MS), "pair": pair, "side": side, "price": price,
                           "units": round(ps.units if side == "buy" else units, 8), "eur": round(eur, 2),
                           "fee": round(fee, 4), "rule": rule.name})
        ps.last_ms = ms

    pot = sum(ps.cash + ps.units * latest[p][1] for p, ps in state.pairs.items() if p in latest)
    for t in trades:
        t["pot_eur"] = round(pot, 2)
        append_csv(trades_file, TRADE_FIELDS, t)
    if latest:
        append_csv(equity_file, EQUITY_FIELDS, {
            "ts_utc": iso(now_ms), "candle_ms": max(ms for ms, _ in latest.values()), "pot_eur": round(pot, 4),
            "closes": json.dumps({p: c for p, (_, c) in latest.items()}), "missed_hours": missed})
    state.last_ok = iso(now_ms)
    state.last_error = None
    save_state(state, state_file)
    return trades


# ---------- weekly report ----------

def report(now_ms: int, days: int = 7, cfg: Config | None = None, state_file: Path = STATE_FILE,
           trades_file: Path = TRADES_FILE, equity_file: Path = EQUITY_FILE) -> dict:
    cfg = cfg or load_config()
    rows = read_csv(equity_file)
    start_ms = now_ms - days * 24 * HOUR_MS
    window = [r for r in rows if int(r["candle_ms"]) >= start_ms - HOUR_MS]
    out: dict = {"days": days, "rule": cfg.active.name, "start_eur": cfg.start_eur}
    state = load_state(cfg, state_file)
    out["health"] = {"last_ok": state.last_ok, "last_error": state.last_error,
                     "hours_recorded": len(window), "hours_expected": days * 24,
                     "missed_hours": sum(int(r["missed_hours"]) for r in window)}
    if not window:
        out["note"] = "no market-watch data in this window"
        return out

    def change(first: dict, last: dict) -> tuple[float, float]:
        pot = (float(last["pot_eur"]) / float(first["pot_eur"]) - 1) * 100
        a, b = json.loads(first["closes"]), json.loads(last["closes"])
        market = sum(b[p] / a[p] - 1 for p in a if p in b) / len(a) * 100
        return round(pot, 2), round(market, 2)

    pot_w, market_w = change(window[0], window[-1])
    pot_all, market_all = change(rows[0], rows[-1])
    trades = [t for t in read_csv(trades_file) if t["ts_utc"] >= iso(start_ms)]
    out.update({
        "pot_eur": round(float(window[-1]["pot_eur"]), 2),
        "week": {"pot_pct": pot_w, "market_pct": market_w, "diff_pp": round(pot_w - market_w, 2)},
        "since_start": {"from": rows[0]["ts_utc"], "pot_pct": pot_all, "market_pct": market_all,
                        "diff_pp": round(pot_all - market_all, 2),
                        "vs_start_eur_pct": round((float(rows[-1]["pot_eur"]) / cfg.start_eur - 1) * 100, 2)},
        "trades": trades,
        "flag_divergence": abs(pot_w - market_w) > cfg.divergence_pp,
    })
    return out


# ---------- backtest (learning) ----------

def history(pair: str, days: int, now_ms: int, fetch: Fetch = http_get, cache_dir: Path = LOG_DIR) -> list[float]:
    """Hourly closes for the last `days`, cached so repeated backtests stay cheap."""
    path = cache_dir / f"crypto_history_{pair}.csv"
    rows = [(int(r["ms"]), float(r["close"])) for r in read_csv(path)]
    start = now_ms - days * 24 * HOUR_MS
    if not rows or rows[0][0] > start + HOUR_MS:
        rows = []
    fresh = fetch_closes(pair, rows[-1][0] + HOUR_MS if rows else start, now_ms, fetch)
    rows += fresh
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ms", "close"])
        w.writerows(rows)
    return [c for ms, c in rows if ms >= start]


def backtest(series: dict[str, list[float]], rules: list[Rule], fee: float, split: float = 0.7,
             seed: int = 7) -> dict:
    """Pick the best rule on the first part (train), judge it on the rest (test).
    Only the test score says anything about the future."""
    def score(rule: Rule, part: str) -> tuple[float, int]:
        rets, trades = [], 0
        for closes in series.values():
            cut = int(len(closes) * split)
            lo, hi = (0, cut) if part == "train" else (cut, len(closes))
            value, n = simulate(closes, signals(closes, rule), lo, hi, 1.0, fee)
            rets.append((value - 1) * 100)
            trades += n
        return round(sum(rets) / len(rets), 2), trades

    def hold(part: str) -> float:
        rets = []
        for closes in series.values():
            cut = int(len(closes) * split)
            a, b = (closes[0], closes[cut - 1]) if part == "train" else (closes[cut], closes[-1])
            rets.append((b / a - 1) * 100)
        return round(sum(rets) / len(rets), 2)

    results = []
    for r in rules:
        tr, tr_n = score(r, "train")
        te, te_n = score(r, "test")
        results.append({"rule": r.name, "train_pct": tr, "test_pct": te, "train_trades": tr_n, "test_trades": te_n})
    best = max(results, key=lambda x: x["train_pct"])

    # Coin-flip baseline: random in/out switches at the same rate as the best rule.
    rng = random.Random(seed)
    flips = []
    for _ in range(200):
        rets = []
        for closes in series.values():
            cut = int(len(closes) * split)
            p = max(best["test_trades"] / max(len(series), 1), 1) / max(len(closes) - cut, 1)
            state, desired = False, []
            for _ in closes:
                if rng.random() < p:
                    state = not state
                desired.append(state)
            value, _ = simulate(closes, desired, cut, len(closes), 1.0, fee)
            rets.append((value - 1) * 100)
        flips.append(sum(rets) / len(rets))
    return {"best_on_train": best, "buy_hold": {"train_pct": hold("train"), "test_pct": hold("test")},
            "coin_flip_test_median_pct": round(median(flips), 2), "all": results}


def activate(name: str, approved: bool, reason: str, today: str, path: Path = CONFIG_FILE) -> Rule:
    if not approved:
        raise PermissionError("changing the market-watch rule needs Tim's approval (--approved)")
    rule = next((r for r in candidate_rules() if r.name == name), None)
    if rule is None:
        raise ValueError(f"unknown rule {name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["active"] = rule.model_dump()
    data["history"].append({"date": today, "rule": name, "reason": reason, "approved_by": "Tim"})
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return rule


# ---------- launchd ----------

def plist_text(project: Path, python: Path) -> str:
    log = project / "logs" / "crypto_watch.log"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{LAUNCHD_LABEL}</string>
  <key>ProgramArguments</key>
  <array><string>{python}</string><string>-m</string><string>tools.crypto</string><string>tick</string></array>
  <key>WorkingDirectory</key><string>{project}</string>
  <key>StartInterval</key><integer>3600</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>{log}</string>
  <key>StandardErrorPath</key><string>{log}</string>
</dict>
</plist>
"""


def plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"


def install_watch(project: Path) -> Path:
    path = plist_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plist_text(project, project / ".venv" / "bin" / "python"), encoding="utf-8")
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", domain, str(path)], check=False, capture_output=True)
    subprocess.run(["launchctl", "bootstrap", domain, str(path)], check=True)
    return path


def uninstall_watch() -> Path:
    # Disable, never delete: the plist is renamed so it can be restored.
    path = plist_path()
    subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}", str(path)], check=False)
    disabled = path.with_suffix(".plist.disabled")
    if path.exists():
        path.rename(disabled)
    return disabled


def now_ms() -> int:
    return int(datetime.now(UTC).timestamp() * 1000)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tools.crypto")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tick")
    rp = sub.add_parser("report")
    rp.add_argument("--days", type=int, default=7)
    bp = sub.add_parser("backtest")
    bp.add_argument("--days", type=int, default=730)
    ac = sub.add_parser("activate")
    ac.add_argument("name")
    ac.add_argument("--reason", required=True)
    ac.add_argument("--approved", action="store_true")
    sub.add_parser("install-watch")
    sub.add_parser("uninstall-watch")
    args = ap.parse_args(argv)

    if args.cmd == "tick":
        trades = tick(now_ms())
        print(f"{iso(now_ms())} ok, {len(trades)} paper trade(s)")
    elif args.cmd == "report":
        print(json.dumps(report(now_ms(), args.days), indent=2, ensure_ascii=False))
    elif args.cmd == "backtest":
        cfg = load_config()
        series = {p: history(p, args.days, now_ms()) for p in cfg.pairs}
        rules = candidate_rules()
        res = backtest(series, rules, cfg.fee_rate)
        active = next((x for x in res["all"] if x["rule"] == cfg.active.name), None)
        res["active"] = active
        res["hours_per_pair"] = {p: len(s) for p, s in series.items()}
        print(json.dumps(res, indent=2))
    elif args.cmd == "activate":
        rule = activate(args.name, args.approved, args.reason, datetime.now(UTC).date().isoformat())
        print(f"active rule is now {rule.name}")
    elif args.cmd == "install-watch":
        print(f"installed {install_watch(Path.cwd().resolve())}")
    elif args.cmd == "uninstall-watch":
        print(f"disabled, kept as {uninstall_watch()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
