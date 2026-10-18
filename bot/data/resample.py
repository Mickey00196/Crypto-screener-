"""Resample OHLCV candles to a higher timeframe.

Coinbase has no weekly candles, so the setup scanner fetches daily bars and
builds weekly ones here. Weeks start Monday 00:00 UTC, matching TradingView's
weekly candles."""

from __future__ import annotations

import pandas as pd

RULES = {
    "1w": "W-MON",
    "1d": "1D",
}

_AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}


def resample_ohlcv(df: pd.DataFrame, timeframe: str = "1w") -> pd.DataFrame:
    """Aggregate a [timestamp, open, high, low, close, volume] frame. The last
    bucket may be incomplete (the current, still-forming week) — callers that
    need only closed candles should drop it."""
    if timeframe not in RULES:
        raise ValueError(f"unsupported timeframe {timeframe!r}; choose one of {sorted(RULES)}")
    if df.empty:
        return df.copy()

    indexed = df.set_index("timestamp").sort_index()
    out = indexed.resample(RULES[timeframe], label="left", closed="left").agg(_AGG)
    out = out.dropna(subset=["open"])
    return out.reset_index()
