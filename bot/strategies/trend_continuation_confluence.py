"""Family 3: trend-continuation confluence.

Mechanism / rationale per indicator:
  - EMA(fast)/EMA(slow) cross — TREND category. Establishes the prevailing
    direction (fast above slow = uptrend) and is what the position HOLDS
    by — exits the moment the cross reverses.
  - MACD histogram — TREND/MOMENTUM category, used here specifically for its
    histogram (momentum-of-momentum) property, not stacked redundantly with
    the EMA cross: requires the histogram to already agree with the EMA
    direction (positive in an uptrend) as a momentum-confirmation filter,
    not a second independent trend read.
  - RSI(rsi_period) — MOMENTUM category. Entry gate: requires a SHALLOW
    pullback within the trend (rsi_pullback threshold much closer to 50 than
    Family 1's deep oversold threshold) — i.e. "buy the dip," never chase
    the breakout at a poor entry price, which is the documented weakness of
    pure trend/breakout entries (RESEARCH.md §2.1).
  - ATR — VOLATILITY category, used by risk/risk_manager.py (shared infra)
    for stop/target sizing.

Symmetric long/short (mirrors Family 1's mechanism but without Family 1's
long-only mean-reversion framing — this is closer to textbook trend
following with an added pullback entry gate)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.momentum import rsi
from indicators.trend import ema, macd


class TrendContinuationConfluenceStrategy:
    def __init__(
        self,
        ema_fast: int = 20,
        ema_slow: int = 50,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        rsi_period: int = 14,
        rsi_pullback_long: float = 50.0,
        rsi_pullback_short: float = 50.0,
    ):
        self.params = {
            "ema_fast": ema_fast,
            "ema_slow": ema_slow,
            "macd_fast": macd_fast,
            "macd_slow": macd_slow,
            "macd_signal": macd_signal,
            "rsi_period": rsi_period,
            "rsi_pullback_long": rsi_pullback_long,
            "rsi_pullback_short": rsi_pullback_short,
        }

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        fast_ema = ema(close, self.params["ema_fast"])
        slow_ema = ema(close, self.params["ema_slow"])
        trend_up = fast_ema > slow_ema
        trend_down = fast_ema < slow_ema

        macd_df = macd(close, self.params["macd_fast"], self.params["macd_slow"], self.params["macd_signal"])
        momentum_up = macd_df["histogram"] > 0
        momentum_down = macd_df["histogram"] < 0

        rsi_line = rsi(close, self.params["rsi_period"])
        pullback_long = rsi_line < self.params["rsi_pullback_long"]
        pullback_short = rsi_line > self.params["rsi_pullback_short"]

        long_entry = trend_up & momentum_up & pullback_long
        short_entry = trend_down & momentum_down & pullback_short

        n = len(df)
        signal = np.zeros(n, dtype=int)
        position = 0
        for i in range(n):
            if pd.isna(trend_up.iloc[i]) or pd.isna(rsi_line.iloc[i]) or pd.isna(momentum_up.iloc[i]):
                signal[i] = 0
                position = 0
                continue
            if position == 1:
                if not bool(trend_up.iloc[i]):
                    position = 0
            elif position == -1:
                if not bool(trend_down.iloc[i]):
                    position = 0
            else:
                if bool(long_entry.iloc[i]):
                    position = 1
                elif bool(short_entry.iloc[i]):
                    position = -1
            signal[i] = position

        return pd.Series(signal, index=df.index)
