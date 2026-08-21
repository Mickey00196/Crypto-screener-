import pandas as pd

from data.synthetic import generate_synthetic_ohlcv
from evaluation.walk_forward import generate_walk_forward_windows, purged_kfold_splits


def test_walk_forward_windows_are_chronological_and_non_overlapping_with_test():
    df = generate_synthetic_ohlcv(n_bars=2000, timeframe="1h", regime="mixed", seed=9)
    windows = generate_walk_forward_windows(
        df,
        train_period=pd.Timedelta(days=30),
        test_period=pd.Timedelta(days=7),
        step=pd.Timedelta(days=7),
        embargo=pd.Timedelta(hours=6),
    )
    assert len(windows) >= 3  # Definition-of-Done requires >=3 windows
    for w in windows:
        assert w.train_end <= w.test_start
        assert w.train["timestamp"].max() < w.test["timestamp"].min()
        assert w.train["timestamp"].max() < w.train_end
        assert w.test["timestamp"].min() >= w.test_start


def test_walk_forward_windows_advance_by_step():
    df = generate_synthetic_ohlcv(n_bars=2000, timeframe="1h", regime="mixed", seed=9)
    windows = generate_walk_forward_windows(
        df,
        train_period=pd.Timedelta(days=30),
        test_period=pd.Timedelta(days=7),
        step=pd.Timedelta(days=7),
    )
    for a, b in zip(windows, windows[1:], strict=False):
        assert b.train_start == a.train_start + pd.Timedelta(days=7)


def test_walk_forward_empty_df_returns_no_windows():
    df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    windows = generate_walk_forward_windows(
        df, train_period=pd.Timedelta(days=1), test_period=pd.Timedelta(days=1), step=pd.Timedelta(days=1)
    )
    assert windows == []


def test_purged_kfold_splits_cover_all_rows_across_test_folds():
    df = generate_synthetic_ohlcv(n_bars=500, timeframe="1h", regime="mixed", seed=9)
    folds = purged_kfold_splits(df, n_splits=5, embargo_frac=0.02)
    assert len(folds) == 5
    test_lengths = sum(len(test) for _, test in folds)
    assert test_lengths == len(df)  # every row appears in exactly one test fold


def test_purged_kfold_embargo_removes_boundary_rows_from_train():
    df = generate_synthetic_ohlcv(n_bars=500, timeframe="1h", regime="mixed", seed=9)
    folds_no_embargo = purged_kfold_splits(df, n_splits=5, embargo_frac=0.0)
    folds_with_embargo = purged_kfold_splits(df, n_splits=5, embargo_frac=0.05)
    # embargo strictly shrinks (or keeps equal for edge folds) the train set
    for (train_no, _), (train_with, _) in zip(folds_no_embargo, folds_with_embargo, strict=True):
        assert len(train_with) <= len(train_no)
