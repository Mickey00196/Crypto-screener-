"""Deterministic weekly candle series for the setup tests.

Closes are linear between waypoints; each candle opens at the previous
close, with 3% wicks unless a high/low is pinned. aero_like() mirrors AERO
weekly from Jul 2025 to mid-Oct 2026 as traced from the TradingView chart:
1.58 high, 1.30 lower high, a 0.29-0.60 base with rising lows (0.29, 0.32,
0.40), a breakout to 1.00 and a pullback to 0.79."""

from __future__ import annotations

import numpy as np
import pandas as pd

WICK = 0.03


def build_series(
    waypoints: dict[int, float],
    highs: dict[int, float] | None = None,
    lows: dict[int, float] | None = None,
    start: str = "2025-06-30",
) -> pd.DataFrame:
    idx = sorted(waypoints)
    n = idx[-1] + 1
    closes = np.interp(np.arange(n), idx, [waypoints[i] for i in idx])
    opens = np.concatenate([[closes[0] * 0.98], closes[:-1]])
    # The open side gets half a wick so a turning-point candle's extreme is
    # never tied by the next candle (which opens at that same close).
    hi = np.maximum(closes * (1 + WICK), opens * (1 + WICK / 2))
    lo = np.minimum(closes * (1 - WICK), opens * (1 - WICK / 2))
    for i, v in (highs or {}).items():
        hi[i] = max(v, opens[i], closes[i])
    for i, v in (lows or {}).items():
        lo[i] = min(v, opens[i], closes[i])
    return pd.DataFrame(
        {
            "timestamp": pd.date_range(start, periods=n, freq="W-MON", tz="UTC"),
            "open": opens,
            "high": hi,
            "low": lo,
            "close": closes,
            "volume": np.full(n, 1_000.0),
        }
    )


AERO_WAYPOINTS = {
    0: 0.92, 4: 1.45, 12: 0.98, 14: 1.15, 23: 0.48, 27: 0.33, 30: 0.30, 36: 0.34,
    41: 0.52, 45: 0.36, 49: 0.57, 54: 0.43, 60: 0.92, 62: 0.95, 63: 0.79,
}  # fmt: skip
AERO_HIGHS = {4: 1.58, 14: 1.30, 41: 0.55, 49: 0.60, 62: 1.00}
AERO_LOWS = {11: 0.75, 30: 0.29, 45: 0.32, 54: 0.40}


def aero_like(last_close: float | None = None) -> pd.DataFrame:
    waypoints = dict(AERO_WAYPOINTS)
    if last_close is not None:
        waypoints[63] = last_close
    return build_series(waypoints, AERO_HIGHS, AERO_LOWS)


def range_bound(last_close: float = 88.0) -> pd.DataFrame:
    """BTC-like range with rising lows (70, 74, 78) and highs (88, 90, 93),
    price still inside it."""
    return build_series(
        {0: 76, 10: 70, 17: 88, 25: 74, 33: 90, 40: 78, 47: 93, 52: last_close},
        start="2025-09-01",
    )


def downtrend() -> pd.DataFrame:
    return build_series({0: 100, 8: 80, 12: 88, 20: 60, 24: 68, 32: 40, 40: 35}, start="2025-09-01")
