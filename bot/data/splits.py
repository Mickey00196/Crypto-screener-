"""Computes chronological train/val/holdout boundaries and writes them to
config/holdout.yaml — the sole source of truth read by guard/holdout_guard.py
and data/storage.py::load_split. Boundaries are computed per symbol/timeframe
since bar counts differ across timeframes."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


def compute_split_boundaries(df: pd.DataFrame, train_frac: float = 0.6, val_frac: float = 0.2) -> dict:
    if not 0 < train_frac < 1 or not 0 < val_frac < 1 or train_frac + val_frac >= 1:
        raise ValueError("train_frac and val_frac must be in (0,1) and sum to < 1")
    n = len(df)
    if n < 10:
        raise ValueError(f"need at least 10 bars to compute a meaningful split, got {n}")
    train_end_idx = int(n * train_frac)
    val_end_idx = int(n * (train_frac + val_frac))
    return {
        "train_end": df["timestamp"].iloc[train_end_idx].isoformat(),
        "val_end": df["timestamp"].iloc[val_end_idx].isoformat(),
        "holdout_end": df["timestamp"].iloc[-1].isoformat(),
    }


def write_holdout_config(all_boundaries: dict[str, dict[str, dict]], path: str | Path) -> Path:
    """all_boundaries: {symbol: {timeframe: {train_end, val_end, holdout_end}}}"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump({"splits": all_boundaries}, f, sort_keys=True)
    return path


def build_holdout_config_from_storage(
    symbols: list[str],
    timeframes: list[str],
    train_frac: float,
    val_frac: float,
    output_path: str | Path,
) -> Path:
    """Loads each symbol/timeframe's RAW data (via data.storage.load_raw —
    never load_split, since the boundaries don't exist yet), computes
    boundaries, and writes config/holdout.yaml."""
    from data.storage import load_raw

    all_boundaries: dict[str, dict[str, dict]] = {}
    for symbol in symbols:
        all_boundaries[symbol] = {}
        for tf in timeframes:
            df = load_raw(symbol, tf)
            all_boundaries[symbol][tf] = compute_split_boundaries(df, train_frac, val_frac)
    return write_holdout_config(all_boundaries, output_path)
