"""OHLCV validation: dedup, monotonic-timestamp assertion, gap detection."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

_TIMEFRAME_UNIT_MAP = {"m": "min", "h": "h", "d": "D"}


@dataclass
class ValidationReport:
    n_bars: int
    duplicates_removed: int
    is_monotonic: bool
    gaps: list[dict] = field(default_factory=list)

    @property
    def total_missing_bars(self) -> int:
        return sum(g["n_missing_bars"] for g in self.gaps)


def timeframe_to_timedelta(timeframe: str) -> pd.Timedelta:
    unit = timeframe[-1]
    n = int(timeframe[:-1])
    if unit not in _TIMEFRAME_UNIT_MAP:
        raise ValueError(f"unsupported timeframe unit in {timeframe!r}")
    return pd.Timedelta(f"{n}{_TIMEFRAME_UNIT_MAP[unit]}")


def validate_ohlcv(df: pd.DataFrame, timeframe: str) -> tuple[pd.DataFrame, ValidationReport]:
    """Dedup by timestamp, sort, assert strictly monotonic, detect gaps
    (missing expected bars given the timeframe's expected spacing — treated
    as exchange downtime windows, not errors)."""
    before = len(df)
    df = df.drop_duplicates(subset="timestamp").sort_values("timestamp").reset_index(drop=True)
    duplicates_removed = before - len(df)

    diffs = df["timestamp"].diff().dropna()
    is_monotonic = bool((diffs > pd.Timedelta(0)).all())
    if not is_monotonic:
        raise ValueError("timestamps are not strictly monotonic increasing after dedup/sort")

    expected_delta = timeframe_to_timedelta(timeframe)
    gaps = []
    for i, d in diffs.items():
        if d > expected_delta:
            n_missing = int(round(d / expected_delta)) - 1
            gaps.append(
                {
                    "start": df["timestamp"].iloc[i - 1],
                    "end": df["timestamp"].iloc[i],
                    "n_missing_bars": n_missing,
                }
            )

    report = ValidationReport(
        n_bars=len(df),
        duplicates_removed=duplicates_removed,
        is_monotonic=is_monotonic,
        gaps=gaps,
    )
    return df, report
