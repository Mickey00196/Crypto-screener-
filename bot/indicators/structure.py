"""Structure indicators: pivots, swing points, fib levels, prior-period
highs/lows, round numbers. Per RESEARCH.md, these are used (in this repo)
for their "where stops/resting orders cluster" mechanism, not as standalone
predictive signals — none of the 3 chosen strategies consume them directly
this pass, but they're implemented and tested per the Phase 2b requirement."""

from __future__ import annotations

import numpy as np
import pandas as pd


def prior_period_high_low(df: pd.DataFrame, freq: str = "1D") -> pd.DataFrame:
    """Attaches the COMPLETED prior period's (day/week) high and low to
    every bar in the following period — never the still-forming current
    period's high/low, which would be a lookahead leak."""
    indexed = df.set_index("timestamp").sort_index()
    period_hl = indexed.resample(freq).agg({"high": "max", "low": "min"}).shift(1)
    period_hl.columns = ["prior_period_high", "prior_period_low"]
    aligned = period_hl.reindex(indexed.index, method="ffill")
    return aligned.reset_index()


def pivot_points(df: pd.DataFrame, freq: str = "1D") -> pd.DataFrame:
    """Classic floor-trader pivot points computed from the prior completed
    period's high/low/close, held constant through the following period."""
    indexed = df.set_index("timestamp").sort_index()
    prior = indexed.resample(freq).agg({"high": "max", "low": "min", "close": "last"}).shift(1)

    pp = (prior["high"] + prior["low"] + prior["close"]) / 3
    r1 = 2 * pp - prior["low"]
    s1 = 2 * pp - prior["high"]
    r2 = pp + (prior["high"] - prior["low"])
    s2 = pp - (prior["high"] - prior["low"])
    r3 = prior["high"] + 2 * (pp - prior["low"])
    s3 = prior["low"] - 2 * (prior["high"] - pp)

    levels = pd.DataFrame({"pp": pp, "r1": r1, "r2": r2, "r3": r3, "s1": s1, "s2": s2, "s3": s3})
    aligned = levels.reindex(indexed.index, method="ffill")
    return aligned.reset_index()


def swing_high_low(df: pd.DataFrame, k: int = 2) -> pd.DataFrame:
    """Fractal swing points: bar i is a swing high if high[i] is the max of
    [i-k, i+k]. NOTE: this cannot be known until k bars AFTER the pivot bar
    (you need the k right-side bars to confirm it) — a strategy consuming
    this must shift it forward by k bars before use, or it is a lookahead
    bug. Provided here as the raw indicator per the Phase 2b requirement;
    none of this repo's 3 chosen strategies consume it directly."""
    high, low = df["high"], df["low"]
    is_swing_high = pd.Series(False, index=df.index)
    is_swing_low = pd.Series(False, index=df.index)
    n = len(df)
    for i in range(k, n - k):
        window_high = high.iloc[i - k : i + k + 1]
        window_low = low.iloc[i - k : i + k + 1]
        if high.iloc[i] == window_high.max() and (window_high == window_high.max()).sum() == 1:
            is_swing_high.iloc[i] = True
        if low.iloc[i] == window_low.min() and (window_low == window_low.min()).sum() == 1:
            is_swing_low.iloc[i] = True
    return pd.DataFrame({"swing_high": is_swing_high, "swing_low": is_swing_low})


def fib_retracement_levels(high: float, low: float) -> dict[str, float]:
    diff = high - low
    return {
        "0.0": high,
        "0.236": high - 0.236 * diff,
        "0.382": high - 0.382 * diff,
        "0.5": high - 0.5 * diff,
        "0.618": high - 0.618 * diff,
        "0.786": high - 0.786 * diff,
        "1.0": low,
    }


def round_number_levels(price: float, step: float = 1000.0) -> dict[str, float]:
    return {"lower": float(np.floor(price / step) * step), "upper": float(np.ceil(price / step) * step)}
