"""Trend indicators. Every function is trailing-only (rolling/ewm over past
bars) — none may reference future rows, since these feed strategies that are
checked by engine/lookahead_check.py."""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Classic MACD: EMA(fast) - EMA(slow), a signal EMA of that line, and
    the histogram (macd - signal)."""
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "histogram": histogram})


def _wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    """Wilder's smoothing: equivalent to an EMA with alpha=1/period, seeded
    by a simple average of the first `period` VALID (non-NaN) values, with
    the seed placed `period` positions after the first valid value. This is
    DIFFERENT from a standard EMA (alpha=2/(period+1)) and from a simple
    rolling mean — the brief explicitly flags this as a common source of
    silently-wrong indicators (RSI/ATR/ADX). Leading NaNs (e.g. from a
    preceding .diff() or .shift()) are skipped, not averaged in as zero."""
    values = series.to_numpy(dtype=float)
    n = len(values)
    out = np.full(n, np.nan)
    valid_mask = ~np.isnan(values)
    if valid_mask.sum() < period:
        return pd.Series(out, index=series.index)
    start = int(np.argmax(valid_mask))
    seed_end = start + period
    if seed_end > n:
        return pd.Series(out, index=series.index)
    out[seed_end - 1] = float(np.mean(values[start:seed_end]))
    for i in range(seed_end, n):
        # (prior*(period-1) + current) / period == prior - prior/period + current/period
        out[i] = out[i - 1] - (out[i - 1] / period) + (values[i] / period)
    return pd.Series(out, index=series.index)


def adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Average Directional Index / +DI / -DI, Wilder's original formulation."""
    high, low, close = df["high"], df["low"], df["close"]
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)

    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)

    smoothed_tr = _wilder_smooth(tr, period)
    smoothed_plus_dm = _wilder_smooth(plus_dm, period)
    smoothed_minus_dm = _wilder_smooth(minus_dm, period)

    plus_di = 100 * (smoothed_plus_dm / smoothed_tr)
    minus_di = 100 * (smoothed_minus_dm / smoothed_tr)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    # NOTE: do not fillna(0) here — dx is genuinely undefined during the
    # +DI/-DI warmup period, and treating that as real zeros would corrupt
    # the Wilder seed average once smoothed below. Let the NaN propagate so
    # _wilder_smooth correctly skips straight to the first valid DX value.
    adx_line = _wilder_smooth(dx, period)

    return pd.DataFrame({"adx": adx_line, "plus_di": plus_di, "minus_di": minus_di})


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder's ATR — the smoothing convention required by the classic
    ATR/ADX/RSI formulas (NOT a simple rolling mean of true range)."""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return _wilder_smooth(tr, period)


def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """ATR-band trend-flip indicator. direction: 1 = uptrend, -1 = downtrend."""
    atr_series = atr(df, period)
    hl2 = (df["high"] + df["low"]) / 2
    upper_band = hl2 + multiplier * atr_series
    lower_band = hl2 - multiplier * atr_series

    close = df["close"].to_numpy()
    n = len(df)
    final_upper = upper_band.to_numpy(dtype=float).copy()
    final_lower = lower_band.to_numpy(dtype=float).copy()
    direction = np.ones(n)
    st = np.full(n, np.nan)

    for i in range(1, n):
        if np.isnan(final_upper[i]) or np.isnan(final_lower[i]):
            continue
        if not np.isnan(final_upper[i - 1]) and (close[i - 1] <= final_upper[i - 1]):
            final_upper[i] = min(final_upper[i], final_upper[i - 1])
        if not np.isnan(final_lower[i - 1]) and (close[i - 1] >= final_lower[i - 1]):
            final_lower[i] = max(final_lower[i], final_lower[i - 1])

        if direction[i - 1] == 1:
            direction[i] = -1 if close[i] < final_lower[i] else 1
        else:
            direction[i] = 1 if close[i] > final_upper[i] else -1

        st[i] = final_lower[i] if direction[i] == 1 else final_upper[i]

    return pd.DataFrame({"supertrend": st, "direction": direction}, index=df.index)


def ichimoku(
    df: pd.DataFrame,
    tenkan_period: int = 9,
    kijun_period: int = 26,
    senkou_b_period: int = 52,
) -> pd.DataFrame:
    high, low = df["high"], df["low"]

    def _midline(period: int) -> pd.Series:
        return (high.rolling(period).max() + low.rolling(period).min()) / 2

    tenkan = _midline(tenkan_period)
    kijun = _midline(kijun_period)
    senkou_a = ((tenkan + kijun) / 2).shift(kijun_period)
    senkou_b = _midline(senkou_b_period).shift(kijun_period)
    chikou = df["close"].shift(-kijun_period)  # plotted in the past, not used as a live signal input
    return pd.DataFrame(
        {"tenkan": tenkan, "kijun": kijun, "senkou_a": senkou_a, "senkou_b": senkou_b, "chikou": chikou}
    )


def donchian(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    upper = df["high"].rolling(window=period, min_periods=period).max()
    lower = df["low"].rolling(window=period, min_periods=period).min()
    middle = (upper + lower) / 2
    return pd.DataFrame({"upper": upper, "lower": lower, "middle": middle})


def linreg_slope(series: pd.Series, period: int = 14) -> pd.Series:
    """Slope of a least-squares line fit over the trailing `period` bars."""
    x = np.arange(period)
    x_mean = x.mean()
    denom = ((x - x_mean) ** 2).sum()

    def _slope(window: np.ndarray) -> float:
        y_mean = window.mean()
        return float(((x - x_mean) * (window - y_mean)).sum() / denom)

    return series.rolling(window=period, min_periods=period).apply(_slope, raw=True)
