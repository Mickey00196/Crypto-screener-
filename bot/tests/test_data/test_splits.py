import pandas as pd
import pytest
import yaml

from data.splits import compute_split_boundaries, write_holdout_config
from data.synthetic import generate_synthetic_ohlcv


def test_split_boundaries_are_chronological():
    df = generate_synthetic_ohlcv(n_bars=1000, timeframe="1h", regime="mixed", seed=1)
    b = compute_split_boundaries(df, 0.6, 0.2)
    train_end = pd.Timestamp(b["train_end"])
    val_end = pd.Timestamp(b["val_end"])
    holdout_end = pd.Timestamp(b["holdout_end"])
    assert train_end < val_end <= holdout_end


def test_split_boundaries_are_roughly_60_20_20():
    df = generate_synthetic_ohlcv(n_bars=1000, timeframe="1h", regime="mixed", seed=1)
    b = compute_split_boundaries(df, 0.6, 0.2)
    train_end = pd.Timestamp(b["train_end"])
    val_end = pd.Timestamp(b["val_end"])
    n = len(df)
    train_frac = (df["timestamp"] < train_end).sum() / n
    val_frac = ((df["timestamp"] >= train_end) & (df["timestamp"] < val_end)).sum() / n
    assert abs(train_frac - 0.6) < 0.02
    assert abs(val_frac - 0.2) < 0.02


def test_rejects_too_few_bars():
    df = generate_synthetic_ohlcv(n_bars=5, timeframe="1h", seed=1)
    with pytest.raises(ValueError):
        compute_split_boundaries(df)


def test_rejects_invalid_fractions():
    df = generate_synthetic_ohlcv(n_bars=100, timeframe="1h", seed=1)
    with pytest.raises(ValueError):
        compute_split_boundaries(df, train_frac=0.7, val_frac=0.4)


def test_write_holdout_config_roundtrip(tmp_path):
    boundaries = {
        "BTC/USDT": {
            "1h": {
                "train_end": "2024-01-01T00:00:00",
                "val_end": "2024-02-01T00:00:00",
                "holdout_end": "2024-03-01T00:00:00",
            }
        }
    }
    path = write_holdout_config(boundaries, tmp_path / "holdout.yaml")
    with open(path) as f:
        loaded = yaml.safe_load(f)
    assert loaded["splits"] == boundaries
