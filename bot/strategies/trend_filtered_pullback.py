"""Family 1 (primary pick, per RESEARCH.md §4): trend-filtered mean-reversion
pullback.

Mechanism / rationale (per indicator — required by the brief's "no
popularity-only rationale" rule):
  - EMA(ema_period) + ADX(adx_period) — TREND category. Together they gate
    entries to only fire when the dominant trend is confirmed up (price
    above a long EMA) AND that trend has real strength (ADX above
    adx_threshold), not chop. This is the mechanism that is supposed to lift
    win rate above naive mean-reversion's: we only buy pullbacks that are
    happening INSIDE a real uptrend, never fading an actual reversal.
  - RSI(rsi_period) — MOMENTUM category. The entry trigger: RSI dropping
    below rsi_entry signals a genuine short-term pullback (temporary
    weakness) worth buying, rather than entering on every bar the trend
    filter is satisfied. RSI rising back above rsi_exit signals the pullback
    has resolved (mean-reverted back up) and it's time to step aside.
  - ATR — VOLATILITY category, used by risk/risk_manager.py (shared infra,
    not duplicated here) to size the stop/target relative to current
    volatility, never a fixed percentage.

Long-only by design (per RESEARCH.md: buying weakness in a confirmed
uptrend has no natural short-side mirror without inverting the whole trend
filter, which would just be Family 3's territory).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.momentum import rsi
from indicators.trend import adx, ema


class TrendFilteredPullbackStrategy:
    def __init__(
        self,
        ema_period: int = 200,
        adx_period: int = 14,
        adx_threshold: float = 20.0,
        rsi_period: int = 14,
        rsi_entry: float = 35.0,
        rsi_exit: float = 55.0,
    ):
        self.params = {
            "ema_period": ema_period,
            "adx_period": adx_period,
            "adx_threshold": adx_threshold,
            "rsi_period": rsi_period,
            "rsi_entry": rsi_entry,
            "rsi_exit": rsi_exit,
        }

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        ema_line = ema(close, self.params["ema_period"])
        adx_df = adx(df, self.params["adx_period"])
        rsi_line = rsi(close, self.params["rsi_period"])

        trend_ok = (close > ema_line) & (adx_df["adx"] > self.params["adx_threshold"])
        entry_trigger = rsi_line < self.params["rsi_entry"]
        exit_trigger = (~trend_ok) | (rsi_line >= self.params["rsi_exit"])

        n = len(df)
        signal = np.zeros(n, dtype=int)
        in_position = False
        for i in range(n):
            if pd.isna(trend_ok.iloc[i]) or pd.isna(rsi_line.iloc[i]):
                signal[i] = 0
                in_position = False
                continue
            if in_position:
                if bool(exit_trigger.iloc[i]):
                    in_position = False
            elif bool(trend_ok.iloc[i]) and bool(entry_trigger.iloc[i]):
                in_position = True
            signal[i] = 1 if in_position else 0

        return pd.Series(signal, index=df.index)
