import numpy as np
import pandas as pd
import pytest

from indicators.trend import (
    _wilder_smooth,
    adx,
    atr,
    donchian,
    ema,
    linreg_slope,
    macd,
    sma,
    supertrend,
)


def test_sma_hand_computed():
    s = pd.Series([1, 2, 3, 4, 5, 6])
    result = sma(s, period=3)
    assert result.iloc[2] == pytest.approx(2.0)  # mean(1,2,3)
    assert result.iloc[3] == pytest.approx(3.0)  # mean(2,3,4)
    assert result.iloc[5] == pytest.approx(5.0)  # mean(4,5,6)
    assert pd.isna(result.iloc[1])


def test_ema_hand_computed():
    # EMA span=3 -> alpha = 2/(3+1) = 0.5. adjust=False recursion:
    # seed = simple mean of first 3 values (pandas ewm with min_periods=3
    # and adjust=False seeds with the first value then recurses — verify
    # against pandas' own formula directly for correctness, not re-derive it)
    s = pd.Series([10.0, 20.0, 30.0, 20.0, 10.0])
    result = ema(s, period=3)
    expected = s.ewm(span=3, adjust=False, min_periods=3).mean()
    pd.testing.assert_series_equal(result, expected)


def test_wilder_smooth_hand_computed_diverges_from_simple_mean():
    """This is THE test the brief calls out: Wilder smoothing must differ
    from a simple rolling mean once the recursion kicks in.

    Recursion: out[i] = (out[i-1]*(period-1) + values[i]) / period.
        seed out[2] = mean(2,4,3) = 3.0
        out[3] = (3.0*2 + 5) / 3 = 11/3
        out[4] = (11/3*2 + 1) / 3 = 25/9
        out[5] = (25/9*2 + 6) / 3 = 104/27
    """
    values = pd.Series([2.0, 4.0, 3.0, 5.0, 1.0, 6.0])
    result = _wilder_smooth(values, period=3)

    assert result.iloc[2] == pytest.approx(3.0)
    assert result.iloc[3] == pytest.approx(11 / 3)
    assert result.iloc[4] == pytest.approx(25 / 9)
    assert result.iloc[5] == pytest.approx(104 / 27)

    simple_mean = values.rolling(3).mean()
    assert result.iloc[3] != pytest.approx(simple_mean.iloc[3])
    assert result.iloc[4] != pytest.approx(simple_mean.iloc[4])


def test_wilder_smooth_skips_leading_nan_correctly():
    values = pd.Series([np.nan, 2.0, 0.0, 2.0, 2.0, 0.0, 2.0])
    result = _wilder_smooth(values, period=3)
    # seed at index 3 = mean(values[1:4]) = mean(2,0,2) = 4/3
    assert result.iloc[3] == pytest.approx(4 / 3)
    assert pd.isna(result.iloc[2])


def test_macd_matches_ema_difference():
    s = pd.Series(np.linspace(100, 150, 60))
    result = macd(s, fast=5, slow=10, signal=4)
    fast_ema = ema(s, 5)
    slow_ema = ema(s, 10)
    pd.testing.assert_series_equal(result["macd"], fast_ema - slow_ema, check_names=False)
    pd.testing.assert_series_equal(
        result["histogram"], result["macd"] - result["signal"], check_names=False
    )


def test_donchian_hand_computed():
    df = pd.DataFrame(
        {
            "high": [10, 12, 9, 15, 11],
            "low": [8, 9, 7, 10, 9],
            "close": [9, 11, 8, 13, 10],
        }
    )
    result = donchian(df, period=3)
    # window covering indices 0-2: high max=12, low min=7
    assert result["upper"].iloc[2] == 12
    assert result["lower"].iloc[2] == 7
    assert result["middle"].iloc[2] == pytest.approx((12 + 7) / 2)
    # window covering indices 2-4: high max=15, low min=7
    assert result["upper"].iloc[4] == 15
    assert result["lower"].iloc[4] == 7


def test_atr_true_range_hand_computed_first_bars():
    df = pd.DataFrame(
        {
            "high": [10, 11, 12],
            "low": [8, 9, 10],
            "close": [9, 10.5, 11],
        }
    )
    result = atr(df, period=2)
    # bar0: no prev close -> TR = high-low = 2
    # bar1: prev_close=9 -> TR = max(11-9=2, |11-9|=2, |9-9|=0) = 2
    # seed at index1 (period=2, start=0): mean(TR[0:2]) = mean(2,2) = 2.0
    assert result.iloc[1] == pytest.approx(2.0)


def test_adx_output_bounded_0_100():
    rng = np.random.default_rng(1)
    n = 100
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, n)))
    high = close + rng.uniform(0.5, 1.5, n)
    low = close - rng.uniform(0.5, 1.5, n)
    df = pd.DataFrame({"high": high, "low": low, "close": close})
    result = adx(df, period=14)
    valid = result["adx"].dropna()
    assert (valid >= 0).all()
    assert (valid <= 100).all()


def test_supertrend_direction_flips_on_strong_move():
    n = 60
    closes = np.concatenate([np.linspace(100, 90, n // 2), np.linspace(90, 130, n // 2)])
    df = pd.DataFrame(
        {
            "high": closes + 0.5,
            "low": closes - 0.5,
            "close": closes,
        }
    )
    result = supertrend(df, period=5, multiplier=2.0)
    directions = result["direction"].dropna().unique()
    assert -1 in directions and 1 in directions


def test_linreg_slope_positive_for_uptrend_negative_for_downtrend():
    up = pd.Series(np.arange(20, dtype=float))
    down = pd.Series(np.arange(20, 0, -1, dtype=float))
    assert linreg_slope(up, period=10).iloc[-1] > 0
    assert linreg_slope(down, period=10).iloc[-1] < 0
