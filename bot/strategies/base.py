"""The strategy plugin interface. Strategies are dumb: they only decide
DIRECTION (long/flat/short) from price/indicator data. Sizing, stops, and
take-profit levels are the risk module's job (risk/risk_manager.py), never
the strategy's — keeping "when to trade" and "how much to risk" separate,
per the brief's Phase 3 requirement."""

from __future__ import annotations

from typing import Protocol

import pandas as pd


class Strategy(Protocol):
    params: dict

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Returns a Series aligned with df's index, one integer per bar:
        1 = long, -1 = short, 0 = flat. MUST be trailing-only — the value at
        index t may depend only on df.iloc[:t+1] (see
        engine/lookahead_check.py, which every strategy here is checked
        against)."""
        ...
