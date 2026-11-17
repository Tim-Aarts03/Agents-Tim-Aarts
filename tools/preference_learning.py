"""Learn Tim's preferences from his 1–5 ratings, deterministically.

For every feature (e.g. `org_type:foundation_nonprofit`) the average rating is
turned into a bonus: a 3 is neutral, a 5 adds points, a 1 subtracts points.
A feature only counts after MIN_RATINGS ratings, so one rating cannot swing
the ranking on its own.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from tools.applications_log import DEFAULT_LOG_PATH, Application, read_log

MIN_RATINGS = 3
NEUTRAL_RATING = 3.0
POINTS_PER_RATING_STEP = 2.5  # avg 5 -> +5, avg 1 -> -5 per feature


def feature_stats(applications: list[Application]) -> dict[str, list[int]]:
    ratings: dict[str, list[int]] = defaultdict(list)
    for app in applications:
        if app.rating is None:
            continue
        for feature in app.feature_list():
            ratings[feature].append(app.rating)
    return dict(ratings)


def feature_bonuses(applications: list[Application]) -> dict[str, float]:
    return {
        feature: (sum(r) / len(r) - NEUTRAL_RATING) * POINTS_PER_RATING_STEP
        for feature, r in feature_stats(applications).items()
        if len(r) >= MIN_RATINGS
    }


def feature_bonuses_from_log(path: Path = DEFAULT_LOG_PATH) -> dict[str, float]:
    return feature_bonuses(read_log(path))


def summary(applications: list[Application]) -> list[str]:
    """Human-readable lines, strongest signals first, for the Friday overview."""
    lines = []
    stats = feature_stats(applications)
    for feature, ratings in sorted(stats.items(), key=lambda kv: -abs(sum(kv[1]) / len(kv[1]) - NEUTRAL_RATING)):
        avg = sum(ratings) / len(ratings)
        status = "actief" if len(ratings) >= MIN_RATINGS else f"nog {MIN_RATINGS - len(ratings)} beoordeling(en) nodig"
        lines.append(f"{feature}: gemiddeld {avg:.1f} uit {len(ratings)} ({status})")
    return lines


def main() -> None:
    """CLI: `python -m tools.preference_learning` prints what has been learned so far."""
    lines = summary(read_log())
    print("\n".join(lines) if lines else "Nog geen beoordelingen.")


if __name__ == "__main__":
    main()
