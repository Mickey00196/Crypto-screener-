"""Family 2: volatility-regime breakout with trend confirmation.

Mechanism / rationale per indicator:
  - Donchian(donchian_period) — VOLATILITY/TREND category. The entry
    trigger: price closing beyond the highest high (or lowest low) of the
    PRIOR `donchian_period` bars (excluding the current bar) is a genuine
    breakout of the recent trading range — the classic turtle-style signal.
  - Supertrend(st_period, st_multiplier) — TREND category. Gates breakouts
    to only fire in the direction Supertrend already agrees with, and — more
    importantly — is what the position HOLDS by: once entered, the position
    stays open only while Supertrend's direction keeps agreeing, giving a
    trend-following exit instead of the single-bar spike a raw breakout
    signal would otherwise produce. This is the mechanism meant to cut the
    high false-breakout rate that drives pure breakout systems' low win
    rate (per RESEARCH.md §2.1).
  - OBV — VOLUME category, confirmation only: requires cumulative volume
    flow to already be moving in the breakout's direction (rising OBV for a
    long breakout), filtering out breakouts on unconvincing volume.
  - ATR — VOLATILITY category, used by risk/risk_manager.py (shared infra)
    for stop/target sizing.

SIMPLIFICATION vs. RESEARCH.md: RESEARCH.md describes a "partial-profit-
then-trail" exit for this family. The engine built this pass supports a
single fixed stop/take-profit per position (engine/backtester.py checks
Position.stop_price/take_profit_price, not a dynamically-updated trailing
stop) — implementing true trailing-stop position updates was out of scope
for this session. This family therefore uses the same fixed ATR stop/target
as Families 1 and 3, which likely understates its real-world win-rate/R:R
profile (this is honestly flagged in RESULTS.md/FINDINGS.md, not hidden)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.trend import donchian, supertrend
from indicators.volume import obv


class VolatilityBreakoutTrendStrategy:
    def __init__(
        self,
        donchian_period: int = 20,
        st_period: int = 10,
        st_multiplier: float = 3.0,
        obv_lookback: int = 5,
    ):
        self.params = {
            "donchian_period": donchian_period,
            "st_period": st_period,
            "st_multiplier": st_multiplier,
            "obv_lookback": obv_lookback,
        }

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        donchian_df = donchian(df, self.params["donchian_period"])
        prior_upper = donchian_df["upper"].shift(1)
        prior_lower = donchian_df["lower"].shift(1)

        st_df = supertrend(df, self.params["st_period"], self.params["st_multiplier"])
        direction = st_df["direction"]

        obv_line = obv(df)
        obv_rising = obv_line.diff(self.params["obv_lookback"]) > 0
        obv_falling = obv_line.diff(self.params["obv_lookback"]) < 0

        breakout_long = (df["close"] > prior_upper) & obv_rising
        breakout_short = (df["close"] < prior_lower) & obv_falling

        n = len(df)
        signal = np.zeros(n, dtype=int)
        position = 0
        for i in range(n):
            if pd.isna(prior_upper.iloc[i]) or pd.isna(direction.iloc[i]):
                signal[i] = 0
                position = 0
                continue
            d = direction.iloc[i]
            if position == 1:
                if d != 1:
                    position = 0
            elif position == -1:
                if d != -1:
                    position = 0
            else:
                if bool(breakout_long.iloc[i]) and d == 1:
                    position = 1
                elif bool(breakout_short.iloc[i]) and d == -1:
                    position = -1
            signal[i] = position

        return pd.Series(signal, index=df.index)
