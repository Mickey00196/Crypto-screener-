"""Walk-forward window generation and purged k-fold cross-validation with an
embargo period — used to check consistency across ≥3 separate windows
(Definition-of-Done requirement) and to detect overfitting via train/val
degradation. Operates only on data already restricted to train+val (never
holdout — callers pass load_split(..., "train_val") output)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class WalkForwardWindow:
    train: pd.DataFrame
    test: pd.DataFrame
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


_ZERO_TIMEDELTA = pd.Timedelta(0)


def generate_walk_forward_windows(
    df: pd.DataFrame,
    train_period: pd.Timedelta,
    test_period: pd.Timedelta,
    step: pd.Timedelta,
    embargo: pd.Timedelta = _ZERO_TIMEDELTA,
) -> list[WalkForwardWindow]:
    """Rolling-origin walk-forward: successive (train, test) windows stepped
    forward by `step`, with an `embargo` gap left between each train window's
    end and its test window's start so indicator lookback (e.g. a 200-bar
    EMA) can't leak information from just-before the boundary."""
    if df.empty:
        return []
    start = df["timestamp"].min()
    end = df["timestamp"].max()

    windows = []
    train_start = start
    while True:
        train_end = train_start + train_period
        test_start = train_end + embargo
        test_end = test_start + test_period
        if test_end > end:
            break
        train_df = df[(df["timestamp"] >= train_start) & (df["timestamp"] < train_end)].reset_index(drop=True)
        test_df = df[(df["timestamp"] >= test_start) & (df["timestamp"] < test_end)].reset_index(drop=True)
        if len(train_df) > 0 and len(test_df) > 0:
            windows.append(WalkForwardWindow(train_df, test_df, train_start, train_end, test_start, test_end))
        train_start += step

    return windows


def purged_kfold_splits(
    df: pd.DataFrame, n_splits: int, embargo_frac: float = 0.01
) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    """Time-ordered k-fold: each fold's contiguous chunk is held out as test;
    an embargo of embargo_frac*len(df) bars on both sides of the test chunk
    is purged from the train set to prevent boundary leakage."""
    if n_splits < 2:
        raise ValueError("n_splits must be >= 2")
    n = len(df)
    fold_size = n // n_splits
    embargo = int(n * embargo_frac)

    folds = []
    for k in range(n_splits):
        test_start = k * fold_size
        test_end = n if k == n_splits - 1 else (k + 1) * fold_size
        purge_start = max(0, test_start - embargo)
        purge_end = min(n, test_end + embargo)
        train_idx = [i for i in range(n) if i < purge_start or i >= purge_end]
        test_df = df.iloc[test_start:test_end].reset_index(drop=True)
        train_df = df.iloc[train_idx].reset_index(drop=True)
        folds.append((train_df, test_df))
    return folds
