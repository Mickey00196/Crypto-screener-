"""Volatility indicators."""

from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.trend import atr


def bollinger_bands(close: pd.Series, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    middle = close.rolling(window=period, min_periods=period).mean()
    std = close.rolling(window=period, min_periods=period).std(ddof=0)
    upper = middle + num_std * std
    lower = middle - num_std * std
    bandwidth = (upper - lower) / middle
    percent_b = (close - lower) / (upper - lower)
    return pd.DataFrame(
        {"upper": upper, "middle": middle, "lower": lower, "bandwidth": bandwidth, "percent_b": percent_b}
    )


def keltner_channels(
    df: pd.DataFrame, period: int = 20, atr_period: int = 10, multiplier: float = 2.0
) -> pd.DataFrame:
    middle = df["close"].ewm(span=period, adjust=False, min_periods=period).mean()
    atr_series = atr(df, atr_period)
    upper = middle + multiplier * atr_series
    lower = middle - multiplier * atr_series
    return pd.DataFrame({"upper": upper, "middle": middle, "lower": lower})


def historical_volatility(
    close: pd.Series, period: int = 20, periods_per_year: float = 24 * 365
) -> pd.Series:
    """Annualized realized volatility of log returns over a trailing window."""
    log_returns = np.log(close / close.shift(1))
    return log_returns.rolling(window=period, min_periods=period).std(ddof=0) * np.sqrt(periods_per_year)
