"""Momentum indicators."""

from __future__ import annotations

import pandas as pd

from indicators.trend import _wilder_smooth


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI (the standard/original formulation — uses Wilder
    smoothing of average gains/losses, NOT a simple rolling mean). This is
    the indicator the brief specifically calls out: a simple-moving-average
    RSI implementation gives visibly different values, which is exactly the
    kind of silently-wrong indicator this module's tests guard against."""
    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = _wilder_smooth(gains, period)
    avg_loss = _wilder_smooth(losses, period)
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    low_min = df["low"].rolling(window=k_period, min_periods=k_period).min()
    high_max = df["high"].rolling(window=k_period, min_periods=k_period).max()
    percent_k = 100 * (df["close"] - low_min) / (high_max - low_min)
    percent_d = percent_k.rolling(window=d_period, min_periods=d_period).mean()
    return pd.DataFrame({"percent_k": percent_k, "percent_d": percent_d})


def stoch_rsi(close: pd.Series, period: int = 14, k_period: int = 3, d_period: int = 3) -> pd.DataFrame:
    rsi_series = rsi(close, period)
    low_min = rsi_series.rolling(window=period, min_periods=period).min()
    high_max = rsi_series.rolling(window=period, min_periods=period).max()
    stoch = 100 * (rsi_series - low_min) / (high_max - low_min)
    k = stoch.rolling(window=k_period, min_periods=k_period).mean()
    d = k.rolling(window=d_period, min_periods=d_period).mean()
    return pd.DataFrame({"stoch_rsi": stoch, "k": k, "d": d})


def cci(df: pd.DataFrame, period: int = 20, constant: float = 0.015) -> pd.Series:
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    sma_tp = typical_price.rolling(window=period, min_periods=period).mean()
    mean_dev = typical_price.rolling(window=period, min_periods=period).apply(
        lambda x: (x - x.mean()).abs().mean(), raw=False
    )
    return (typical_price - sma_tp) / (constant * mean_dev)


def williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_max = df["high"].rolling(window=period, min_periods=period).max()
    low_min = df["low"].rolling(window=period, min_periods=period).min()
    return -100 * (high_max - df["close"]) / (high_max - low_min)


def roc(close: pd.Series, period: int = 10) -> pd.Series:
    return 100 * (close - close.shift(period)) / close.shift(period)
