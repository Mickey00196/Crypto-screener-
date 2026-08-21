import numpy as np
import pandas as pd
import pytest

from indicators.volatility import bollinger_bands, historical_volatility, keltner_channels


def test_bollinger_bands_hand_computed():
    closes = pd.Series([10.0, 12.0, 11.0, 13.0, 9.0])
    result = bollinger_bands(closes, period=5, num_std=2.0)
    mean = closes.mean()  # 11.0
    std = closes.std(ddof=0)  # population std
    assert result["middle"].iloc[-1] == pytest.approx(mean)
    assert result["upper"].iloc[-1] == pytest.approx(mean + 2 * std)
    assert result["lower"].iloc[-1] == pytest.approx(mean - 2 * std)
    # %B at the close: (close - lower) / (upper - lower)
    expected_percent_b = (closes.iloc[-1] - (mean - 2 * std)) / (4 * std)
    assert result["percent_b"].iloc[-1] == pytest.approx(expected_percent_b)


def test_bollinger_bandwidth_zero_for_constant_series():
    closes = pd.Series([10.0] * 10)
    result = bollinger_bands(closes, period=5, num_std=2.0)
    assert result["bandwidth"].iloc[-1] == pytest.approx(0.0)


def test_keltner_channels_bracket_middle():
    n = 50
    rng = np.random.default_rng(3)
    closes = pd.Series(100 + np.cumsum(rng.normal(0, 1, n)))
    df = pd.DataFrame({"high": closes + 1, "low": closes - 1, "close": closes})
    result = keltner_channels(df, period=10, atr_period=5, multiplier=2.0)
    valid = result.dropna()
    assert (valid["upper"] >= valid["middle"]).all()
    assert (valid["lower"] <= valid["middle"]).all()


def test_historical_volatility_zero_for_constant_series():
    closes = pd.Series([100.0] * 30)
    result = historical_volatility(closes, period=10)
    assert result.dropna().eq(0.0).all()


def test_historical_volatility_positive_for_noisy_series():
    rng = np.random.default_rng(4)
    closes = pd.Series(100 + np.cumsum(rng.normal(0, 1, 60)))
    result = historical_volatility(closes, period=10)
    assert (result.dropna() > 0).all()
