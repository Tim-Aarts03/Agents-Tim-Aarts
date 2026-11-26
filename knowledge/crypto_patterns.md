# Crypto patterns logbook (paper trading)

Hypotheses the `invest-crypto-analyst` tracks week by week. A pattern only counts as real after **at least 20 cases over at least 8 weeks**, and only becomes a rule proposal after a test on unseen data. Source of every number: `tools.crypto review` (journal in `logs/crypto_trade_journal.csv`, local).

## P1 — Borderline signals reverse quickly (whipsaw)
Idea: when the 24-hour average is only just above the 7-day average (`buy_margin_pct` < 0.2%), the price often turns back and the rule sells within ~12 hours with a loss plus double fees.
- 2026-11-26: ETH buy 24-11 07:00 UTC, margin 0.074%, sold after 5 h, -€0.62 (fees €0.40). Supports P1.
- Count: 1 supporting, 0 against. Status: te weinig gegevens.

## P2 — Mac sleep changes the trades
Idea: when the watch misses hours, it trades at a different moment than the rule intended; this changes results by luck, not skill.
- 2026-11-26: with full data the rule would have bought 24-11 02:00 (€1561.09) and sold 11:00 (€1537.39); the watch bought at 07:00 (€1559.39) and sold at 12:00 (€1552.41). The late sell got a higher price this time (helped).
- Count: 1 week (helped). Status: te weinig gegevens.

## P3 — Selling after a turn protects the pot
Idea: after a sell signal the coin keeps falling (`after_sell_24h_pct` < 0).
- 2026-11-26: ETH -3.63% in the 24 h after the sell. Supports P3.
- Count: 1 supporting, 0 against. Status: te weinig gegevens.
