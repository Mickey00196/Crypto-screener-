"""Small, self-contained Strategy-protocol implementations used only by
engine tests — deliberately independent of the real strategies/ package
(built in Phase 3) so the engine can be built and proven correct first."""

from __future__ import annotations

import pandas as pd

from engine.types import Position, Side, SizeDecision


class EMACrossStrategy:
    """Clean, trailing-only trend strategy: long when fast EMA > slow EMA."""

    def __init__(self, fast: int = 3, slow: int = 8):
        self.params = {"fast": fast, "slow": slow}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        fast_ema = df["close"].ewm(span=self.params["fast"], adjust=False).mean()
        slow_ema = df["close"].ewm(span=self.params["slow"], adjust=False).mean()
        return (fast_ema > slow_ema).astype(int)


class AlwaysShortStrategy:
    """Always attempts to be short, regardless of price action."""

    def __init__(self):
        self.params: dict = {}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        return pd.Series(-1, index=df.index)


class ScriptedStrategy:
    """Replays a fixed, hand-authored signal sequence — used by the
    known-answer test where exact fill prices must be hand-computable."""

    def __init__(self, signals: list[int]):
        self.params = {"signals": signals}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if len(self.params["signals"]) != len(df):
            raise ValueError("scripted signal length must match df length")
        return pd.Series(self.params["signals"], index=df.index)


class LookaheadBuggyStrategy:
    """Deliberately broken: peeks at the NEXT bar's close via shift(-1).
    Used as the positive control for the lookahead detector — the detector
    MUST raise LookaheadError against this strategy."""

    def __init__(self):
        self.params: dict = {}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        future_close = df["close"].shift(-1)
        return (future_close > df["close"]).astype(int).fillna(0)


class FixedRiskManager:
    """Test double: fixed position size, no stop/take-profit, never halts.
    Satisfies engine.types.RiskManagerLike."""

    def __init__(self, size: float = 1.0):
        self.size = size

    def decide(
        self,
        side: Side,
        symbol: str,
        df_so_far: pd.DataFrame,
        equity: float,
        open_positions: dict[str, Position],
    ) -> SizeDecision:
        return SizeDecision(size=self.size, stop_price=None, take_profit_price=None)

    def should_halt(self, equity_history: list[float], initial_capital: float) -> bool:
        return False
