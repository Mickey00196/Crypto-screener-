"""Persisted trading-loop state (cash, open positions, trade log, last
processed bar per symbol) so the loop survives restarts. Plain JSON on disk
— simple, human-inspectable, no database dependency for this pass."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class OpenPositionState:
    symbol: str
    side: str  # "long" | "short"
    size: float
    entry_price: float
    entry_time: str
    stop_price: float | None = None
    take_profit_price: float | None = None


@dataclass
class TradingState:
    trading_mode: str
    cash: float
    initial_capital: float
    positions: dict[str, OpenPositionState] = field(default_factory=dict)
    trade_log: list[dict[str, Any]] = field(default_factory=list)
    last_processed_bar_time: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "trading_mode": self.trading_mode,
            "cash": self.cash,
            "initial_capital": self.initial_capital,
            "positions": {k: asdict(v) for k, v in self.positions.items()},
            "trade_log": self.trade_log,
            "last_processed_bar_time": self.last_processed_bar_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TradingState:
        positions = {k: OpenPositionState(**v) for k, v in data.get("positions", {}).items()}
        return cls(
            trading_mode=data["trading_mode"],
            cash=data["cash"],
            initial_capital=data["initial_capital"],
            positions=positions,
            trade_log=data.get("trade_log", []),
            last_processed_bar_time=data.get("last_processed_bar_time", {}),
        )


def save_state(state: TradingState, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(state.to_dict(), indent=2))
    tmp_path.replace(path)  # atomic rename — a crash mid-write never corrupts the live file


def load_state(
    path: str | Path, default_initial_capital: float = 10_000.0, trading_mode: str = "paper"
) -> TradingState:
    path = Path(path)
    if not path.exists():
        return TradingState(
            trading_mode=trading_mode, cash=default_initial_capital, initial_capital=default_initial_capital
        )
    data = json.loads(path.read_text())
    return TradingState.from_dict(data)
