"""Multi-timeframe helpers: resample to a higher timeframe correctly, and
attach higher-timeframe context to a lower-timeframe dataframe using ONLY
already-closed higher-TF bars — e.g. the 4h bar available at 09:15 is the
one that closed at 08:00, never the one still forming. This is the anti-leak
mechanism required by the brief's multi-timeframe combination rule."""

from __future__ import annotations

import pandas as pd

_TF_TO_PANDAS_FREQ = {"5m": "5min", "15m": "15min", "1h": "h", "4h": "4h", "1d": "D"}
_TF_TO_TIMEDELTA = {
    "5m": pd.Timedelta(minutes=5),
    "15m": pd.Timedelta(minutes=15),
    "1h": pd.Timedelta(hours=1),
    "4h": pd.Timedelta(hours=4),
    "1d": pd.Timedelta(days=1),
}


def resample_ohlcv(df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
    """Resamples base-timeframe OHLCV up to `target_timeframe`. Each output
    row's `timestamp` is that higher-TF bar's OPEN time (consistent with the
    base data's convention); `available_at` is its CLOSE time — the moment
    a lower-timeframe consumer is allowed to see it."""
    if target_timeframe not in _TF_TO_PANDAS_FREQ:
        raise ValueError(f"unsupported timeframe {target_timeframe!r}")
    freq = _TF_TO_PANDAS_FREQ[target_timeframe]
    indexed = df.set_index("timestamp").sort_index()
    agg = (
        indexed.resample(freq, label="left", closed="left")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna()
    )
    agg = agg.reset_index()
    agg["available_at"] = agg["timestamp"] + _TF_TO_TIMEDELTA[target_timeframe]
    return agg


def align_higher_timeframe(
    base_df: pd.DataFrame, higher_df: pd.DataFrame, suffix: str = "_htf"
) -> pd.DataFrame:
    """For each base-timeframe row, attaches the most recently CLOSED
    higher-timeframe bar's OHLCV (columns suffixed, e.g. close_htf) — the
    last higher_df row whose available_at <= this base row's timestamp.
    A still-forming higher-TF bar is never visible to an earlier base bar."""
    base_sorted = base_df.sort_values("timestamp").reset_index(drop=True)
    htf_sorted = higher_df.sort_values("available_at").reset_index(drop=True)
    merged = pd.merge_asof(
        base_sorted,
        htf_sorted,
        left_on="timestamp",
        right_on="available_at",
        direction="backward",
        suffixes=("", suffix),
    )
    return merged
