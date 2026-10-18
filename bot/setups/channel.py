"""Rising channel in log price, built the way a chart reader draws one.

1. Anchor on the lowest confirmed swing low in the lookback window.
2. Lower line: through the anchor and the later swing low giving the
   SHALLOWEST slope, so no later swing low sits below the line.
3. The structure window runs from the anchor to the last confirmed swing
   low. The upper line is parallel, through the highest high in that
   window. Highs after the last swing low are what's being measured against
   the channel (a breakout, or still inside), so they don't define it."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from setups.levels import Pivot


@dataclass(frozen=True)
class Channel:
    anchor_index: int
    anchor_price: float
    slope: float  # log-price change per bar
    width: float  # log distance from lower to upper line
    structure_end: int  # index of the last confirmed swing low
    touches: int  # swing lows within tolerance of the lower line

    def lower_at(self, index: int) -> float:
        return float(math.exp(math.log(self.anchor_price) + self.slope * (index - self.anchor_index)))

    def upper_at(self, index: int) -> float:
        return self.lower_at(index) * math.exp(self.width)


def fit_rising_channel(
    df: pd.DataFrame, pivots: list[Pivot], lookback: int = 52, tolerance: float = 0.04
) -> Channel | None:
    start = max(0, len(df) - lookback)
    lows = [p for p in pivots if p.kind == "low" and not p.provisional and p.index >= start]
    if len(lows) < 2:
        return None

    anchor = min(lows, key=lambda p: p.price)
    later = [p for p in lows if p.index > anchor.index]
    if not later:
        return None

    log_a = math.log(anchor.price)
    slope = min((math.log(p.price) - log_a) / (p.index - anchor.index) for p in later)
    if slope <= 0:
        return None

    def line(i: int) -> float:
        return log_a + slope * (i - anchor.index)

    touches = sum(
        1 for p in lows if p.index >= anchor.index and abs(math.log(p.price) - line(p.index)) <= tolerance
    )
    structure_end = max(p.index for p in later)
    idx = np.arange(anchor.index, structure_end + 1)
    highs = np.log(df["high"].to_numpy()[idx])
    width = float(np.max(highs - (log_a + slope * (idx - anchor.index))))
    if width <= 0:
        return None

    return Channel(anchor.index, anchor.price, float(slope), width, structure_end, touches)
