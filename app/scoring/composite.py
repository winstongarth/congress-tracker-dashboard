"""7.6 Composite score (per trade):

composite = w1*performance + w2*overlap + w3*conviction + w4*recency_weight

Weights [CONFIG: default w1=0.35, w2=0.30, w3=0.20, w4=0.15], versioned by
logging every weight change with a timestamp (data/weight_changes.log) so
past rankings stay comparable to current ones.

Interpretive note: overlap and conviction are only defined for *buy* trades
(both are scoped to buying behavior). Sell trades still get a
composite score from their performance + recency components, but with
overlap/conviction defaulted to the population median (50, a neutral
percentile) rather than 0 -- a sell isn't structurally "low conviction",
the concept just doesn't apply to it, and scoring it as 0 would unfairly
tank every sell's composite relative to buys.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from config.settings import settings

WEIGHT_LOG_PATH = Path("data/weight_changes.log")
NEUTRAL_PERCENTILE = 50.0


def current_weights() -> dict[str, float]:
    return {
        "performance": settings.composite_weight_performance,
        "overlap": settings.composite_weight_overlap,
        "conviction": settings.composite_weight_conviction,
        "recency": settings.composite_weight_recency,
    }


def log_weights_if_changed(weights: dict[str, float]) -> None:
    WEIGHT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    last_weights = None
    if WEIGHT_LOG_PATH.exists():
        lines = WEIGHT_LOG_PATH.read_text().strip().splitlines()
        if lines:
            last_weights = json.loads(lines[-1])["weights"]
    if last_weights != weights:
        entry = {"timestamp": dt.datetime.utcnow().isoformat(), "weights": weights}
        with WEIGHT_LOG_PATH.open("a") as f:
            f.write(json.dumps(entry) + "\n")


def compute_composite(
    performance_pct: dict[int, float],
    overlap_pct: dict[int, float],
    conviction_pct: dict[int, float],
    recency_weight: dict[int, float],
) -> dict[int, float]:
    weights = current_weights()
    log_weights_if_changed(weights)

    composite: dict[int, float] = {}
    for trade_id, perf in performance_pct.items():
        overlap = overlap_pct.get(trade_id, NEUTRAL_PERCENTILE)
        conviction = conviction_pct.get(trade_id, NEUTRAL_PERCENTILE)
        recency = recency_weight.get(trade_id, NEUTRAL_PERCENTILE)
        composite[trade_id] = (
            weights["performance"] * perf
            + weights["overlap"] * overlap
            + weights["conviction"] * conviction
            + weights["recency"] * recency
        )
    return composite
