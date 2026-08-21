"""Paper-trading broker: simulates fills against REAL public market data
(fetched live via data/fetch_bitvavo.py) using the SAME CostModel as
backtesting, so paper-mode expectancy is directly comparable to the
backtest's. No API keys, no real orders ever placed — this is the default
and only path exercised when TRADING_MODE=paper (see live/live_broker.py for
the gated real-order path)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from engine.costs import CostModel
from engine.types import Side
from live.state import OpenPositionState, TradingState


@dataclass
class SimulatedFill:
    symbol: str
    side: Side
    size: float
    intended_price: float  # the bar's open — what the backtest/strategy assumed
    actual_price: float  # after simulated slippage — what a real paper fill would look like
    fee: float
    timestamp: pd.Timestamp


class PaperBroker:
    def __init__(self, cost_model: CostModel):
        self.cost_model = cost_model

    def open_position(
        self,
        state: TradingState,
        symbol: str,
        side: Side,
        size: float,
        bar: pd.Series,
        stop_price: float | None = None,
        take_profit_price: float | None = None,
    ) -> SimulatedFill:
        intended_price = float(bar["open"])
        actual_price = self.cost_model.entry_fill_price(intended_price, side)
        fee = self.cost_model.fee(actual_price * size)
        notional = actual_price * size

        if side == Side.LONG:
            state.cash -= notional
        else:
            state.cash += notional
        state.cash -= fee

        state.positions[symbol] = OpenPositionState(
            symbol=symbol,
            side=side.value,
            size=size,
            entry_price=actual_price,
            entry_time=str(bar["timestamp"]),
            stop_price=stop_price,
            take_profit_price=take_profit_price,
        )
        return SimulatedFill(symbol, side, size, intended_price, actual_price, fee, bar["timestamp"])

    def close_position(self, state: TradingState, symbol: str, bar: pd.Series, reason: str) -> SimulatedFill:
        pos = state.positions.pop(symbol)
        side = Side(pos.side)
        intended_price = float(bar["open"])
        actual_price = self.cost_model.exit_fill_price(intended_price, side)
        fee = self.cost_model.fee(actual_price * pos.size)
        notional = actual_price * pos.size

        if side == Side.LONG:
            state.cash += notional
            price_pnl = (actual_price - pos.entry_price) * pos.size
        else:
            state.cash -= notional
            price_pnl = (pos.entry_price - actual_price) * pos.size
        state.cash -= fee

        pnl = price_pnl - fee
        state.trade_log.append(
            {
                "symbol": symbol,
                "side": pos.side,
                "entry_price": pos.entry_price,
                "entry_time": pos.entry_time,
                "exit_price": actual_price,
                "exit_time": str(bar["timestamp"]),
                "size": pos.size,
                "pnl": pnl,
                "exit_reason": reason,
            }
        )
        return SimulatedFill(symbol, side, pos.size, intended_price, actual_price, fee, bar["timestamp"])
