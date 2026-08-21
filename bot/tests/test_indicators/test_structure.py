import pandas as pd
import pytest

from indicators.structure import (
    fib_retracement_levels,
    pivot_points,
    prior_period_high_low,
    round_number_levels,
    swing_high_low,
)


def test_prior_period_high_low_never_leaks_current_day():
    ts = pd.date_range("2024-01-01", periods=48, freq="h", tz="UTC")
    highs = [100.0] * 24 + [95.0] * 24
    highs[5] = 110.0
    lows = [95.0] * 24 + [92.0] * 24
    lows[10] = 90.0
    closes = [98.0] * 48
    df = pd.DataFrame({"timestamp": ts, "high": highs, "low": lows, "close": closes})

    result = prior_period_high_low(df, freq="1D")
    day1 = result.iloc[:24]
    day2 = result.iloc[24:]

    assert day1["prior_period_high"].isna().all()  # no data before day 1
    assert day1["prior_period_low"].isna().all()
    assert (day2["prior_period_high"] == 110.0).all()
    assert (day2["prior_period_low"] == 90.0).all()


def test_pivot_points_hand_computed():
    ts = pd.date_range("2024-01-01", periods=48, freq="h", tz="UTC")
    highs = [100.0] * 24 + [50.0] * 24
    lows = [100.0] * 24 + [50.0] * 24
    closes = [100.0] * 24 + [50.0] * 24
    highs[3] = 120.0
    lows[3] = 80.0
    closes[23] = 105.0
    df = pd.DataFrame({"timestamp": ts, "high": highs, "low": lows, "close": closes})

    result = pivot_points(df, freq="1D")
    day1_high, day1_low, day1_close = 120.0, 80.0, 105.0
    pp = (day1_high + day1_low + day1_close) / 3
    r1 = 2 * pp - day1_low
    s1 = 2 * pp - day1_high

    day2 = result.iloc[24:]
    assert day2["pp"].iloc[0] == pytest.approx(pp)
    assert day2["r1"].iloc[0] == pytest.approx(r1)
    assert day2["s1"].iloc[0] == pytest.approx(s1)


def test_swing_high_low_detects_clear_peak_and_trough():
    highs = pd.Series([1, 2, 3, 10, 3, 2, 1, 2, 3, 4])
    lows = pd.Series([1, 2, 3, 4, 3, 2, 1, -5, 3, 4])
    df = pd.DataFrame({"high": highs, "low": lows})
    result = swing_high_low(df, k=2)
    assert bool(result["swing_high"].iloc[3])
    assert bool(result["swing_low"].iloc[7])
    assert not bool(result["swing_high"].iloc[0])


def test_fib_retracement_levels_hand_computed():
    levels = fib_retracement_levels(high=200.0, low=100.0)
    assert levels["0.0"] == pytest.approx(200.0)
    assert levels["0.5"] == pytest.approx(150.0)
    assert levels["0.618"] == pytest.approx(200 - 0.618 * 100)
    assert levels["1.0"] == pytest.approx(100.0)


def test_round_number_levels_hand_computed():
    levels = round_number_levels(20450.0, step=1000.0)
    assert levels["lower"] == pytest.approx(20000.0)
    assert levels["upper"] == pytest.approx(21000.0)
