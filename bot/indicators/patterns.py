"""Candlestick patterns. Shape-based only (no trend-context filtering here —
per RESEARCH.md, standalone pattern edge is weak/contested in the literature;
these are implemented and tested per the Phase 2b requirement but not used
as a signal leg in any of the 3 chosen strategies this pass)."""

from __future__ import annotations

import pandas as pd


def doji(df: pd.DataFrame, body_threshold: float = 0.1) -> pd.Series:
    body = (df["close"] - df["open"]).abs()
    candle_range = (df["high"] - df["low"]).replace(0, float("nan"))
    return (body / candle_range) <= body_threshold


def inside_bar(df: pd.DataFrame) -> pd.Series:
    prev_high = df["high"].shift(1)
    prev_low = df["low"].shift(1)
    return (df["high"] < prev_high) & (df["low"] > prev_low)


def bullish_engulfing(df: pd.DataFrame) -> pd.Series:
    prev_open, prev_close = df["open"].shift(1), df["close"].shift(1)
    prev_bearish = prev_close < prev_open
    curr_bullish = df["close"] > df["open"]
    engulfs = (df["open"] <= prev_close) & (df["close"] >= prev_open)
    return prev_bearish & curr_bullish & engulfs


def bearish_engulfing(df: pd.DataFrame) -> pd.Series:
    prev_open, prev_close = df["open"].shift(1), df["close"].shift(1)
    prev_bullish = prev_close > prev_open
    curr_bearish = df["close"] < df["open"]
    engulfs = (df["open"] >= prev_close) & (df["close"] <= prev_open)
    return prev_bullish & curr_bearish & engulfs


def hammer(df: pd.DataFrame, body_to_range_max: float = 0.3, lower_wick_min_ratio: float = 2.0) -> pd.Series:
    body = (df["close"] - df["open"]).abs()
    candle_range = (df["high"] - df["low"]).replace(0, float("nan"))
    lower_wick = df[["open", "close"]].min(axis=1) - df["low"]
    upper_wick = df["high"] - df[["open", "close"]].max(axis=1)
    small_body = (body / candle_range) <= body_to_range_max
    long_lower_wick = lower_wick >= lower_wick_min_ratio * body.replace(0, 1e-12)
    small_upper_wick = upper_wick <= body.replace(0, 1e-12)
    return small_body & long_lower_wick & small_upper_wick


def shooting_star(
    df: pd.DataFrame, body_to_range_max: float = 0.3, upper_wick_min_ratio: float = 2.0
) -> pd.Series:
    body = (df["close"] - df["open"]).abs()
    candle_range = (df["high"] - df["low"]).replace(0, float("nan"))
    lower_wick = df[["open", "close"]].min(axis=1) - df["low"]
    upper_wick = df["high"] - df[["open", "close"]].max(axis=1)
    small_body = (body / candle_range) <= body_to_range_max
    long_upper_wick = upper_wick >= upper_wick_min_ratio * body.replace(0, 1e-12)
    small_lower_wick = lower_wick <= body.replace(0, 1e-12)
    return small_body & long_upper_wick & small_lower_wick
