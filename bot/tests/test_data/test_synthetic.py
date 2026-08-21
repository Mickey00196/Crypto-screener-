import pandas as pd

from data.synthetic import generate_deterministic_trend, generate_synthetic_ohlcv


def test_shape_and_columns():
    df = generate_synthetic_ohlcv(n_bars=200, timeframe="1h", seed=1)
    assert len(df) == 200
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]


def test_high_low_bracket_open_close():
    df = generate_synthetic_ohlcv(n_bars=200, timeframe="1h", regime="mixed", seed=1)
    assert (df["high"] >= df[["open", "close"]].max(axis=1)).all()
    assert (df["low"] <= df[["open", "close"]].min(axis=1)).all()


def test_deterministic_with_seed():
    a = generate_synthetic_ohlcv(n_bars=100, seed=7)
    b = generate_synthetic_ohlcv(n_bars=100, seed=7)
    pd.testing.assert_frame_equal(a, b)


def test_different_seeds_differ():
    a = generate_synthetic_ohlcv(n_bars=100, seed=7)
    b = generate_synthetic_ohlcv(n_bars=100, seed=8)
    assert not a["close"].equals(b["close"])


def test_zero_vol_regime_is_constant_and_tradeless():
    df = generate_synthetic_ohlcv(n_bars=50, regime="zero_vol", seed=1)
    assert (df["close"] == df["close"].iloc[0]).all()
    assert (df["high"] == df["close"]).all()
    assert (df["low"] == df["close"]).all()
    assert (df["volume"] == 0).all()


def test_trend_up_regime_net_positive():
    df = generate_synthetic_ohlcv(n_bars=2000, regime="trend_up", seed=3)
    assert df["close"].iloc[-1] > df["close"].iloc[0]


def test_trend_down_regime_net_negative():
    df = generate_synthetic_ohlcv(n_bars=2000, regime="trend_down", seed=3)
    assert df["close"].iloc[-1] < df["close"].iloc[0]


def test_deterministic_trend_is_strictly_monotonic():
    up = generate_deterministic_trend(n_bars=100, direction="up")
    down = generate_deterministic_trend(n_bars=100, direction="down")
    assert up["close"].is_monotonic_increasing
    assert down["close"].is_monotonic_decreasing


def test_deterministic_trend_rejects_bad_direction():
    import pytest

    with pytest.raises(ValueError):
        generate_deterministic_trend(direction="sideways")
