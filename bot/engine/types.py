"""Core dataclasses/interfaces shared across the backtest engine and the
risk module. Keeping these in one neutral module avoids circular imports
between engine/* and risk/risk_manager.py."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

import pandas as pd


class Side(Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class Position:
    symbol: str
    side: Side
    size: float
    entry_price: float
    entry_time: pd.Timestamp
    entry_fee: float
    stop_price: float | None = None
    take_profit_price: float | None = None


@dataclass
class Trade:
    symbol: str
    side: Side
    entry_time: pd.Timestamp
    entry_price: float
    exit_time: pd.Timestamp
    exit_price: float
    size: float
    fees_paid: float  # entry + exit fees combined
    pnl: float  # net of fees
    exit_reason: str  # "signal" | "stop_loss" | "take_profit" | "kill_switch" | "end_of_data"
    risk_per_unit: float | None = None  # |entry_price - stop_price|, for R-multiple calc

    @property
    def r_multiple(self) -> float | None:
        if not self.risk_per_unit or self.risk_per_unit == 0:
            return None
        return self.pnl / (self.risk_per_unit * self.size)


@dataclass
class SizeDecision:
    """What a risk manager decides for a candidate new position. size<=0
    means "do not take this trade"."""

    size: float
    stop_price: float | None = None
    take_profit_price: float | None = None


class RiskManagerLike(Protocol):
    """Interface the backtester depends on. risk/risk_manager.py (Phase 3)
    implements this; engine tests use lightweight stand-ins so the engine
    can be built and tested before the risk module exists."""

    def decide(
        self,
        side: Side,
        symbol: str,
        df_so_far: pd.DataFrame,
        equity: float,
        open_positions: dict[str, Position],
    ) -> SizeDecision: ...

    def should_halt(self, equity_history: list[float], initial_capital: float) -> bool: ...


@dataclass
class BacktestResult:
    trades: list[Trade]
    equity_curve: pd.DataFrame  # columns: timestamp, equity
    initial_capital: float
    final_equity: float
    open_position: Position | None = None
