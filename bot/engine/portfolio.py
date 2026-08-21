"""Cash/position bookkeeping. Supports multiple concurrent positions across
symbols sharing one cash pool (used when Backtester.run_multi backtests
several symbols together); Backtester.run backtests a single symbol at a
time against its own Portfolio instance."""

from __future__ import annotations

from engine.types import Position, Side, Trade


class Portfolio:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []

    def open_position(
        self,
        symbol: str,
        side: Side,
        size: float,
        fill_price: float,
        time,
        fee: float,
        stop_price: float | None = None,
        take_profit_price: float | None = None,
    ) -> Position:
        notional = size * fill_price
        if side == Side.LONG:
            self.cash -= notional
        else:
            self.cash += notional
        self.cash -= fee
        position = Position(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=fill_price,
            entry_time=time,
            entry_fee=fee,
            stop_price=stop_price,
            take_profit_price=take_profit_price,
        )
        self.positions[symbol] = position
        return position

    def close_position(self, symbol: str, fill_price: float, time, fee: float, exit_reason: str) -> Trade:
        pos = self.positions.pop(symbol)
        notional = pos.size * fill_price
        if pos.side == Side.LONG:
            self.cash += notional
            price_pnl = (fill_price - pos.entry_price) * pos.size
        else:
            self.cash -= notional
            price_pnl = (pos.entry_price - fill_price) * pos.size
        self.cash -= fee

        pnl = price_pnl - pos.entry_fee - fee
        risk_per_unit = abs(pos.entry_price - pos.stop_price) if pos.stop_price is not None else None
        trade = Trade(
            symbol=symbol,
            side=pos.side,
            entry_time=pos.entry_time,
            entry_price=pos.entry_price,
            exit_time=time,
            exit_price=fill_price,
            size=pos.size,
            fees_paid=pos.entry_fee + fee,
            pnl=pnl,
            exit_reason=exit_reason,
            risk_per_unit=risk_per_unit,
        )
        self.trades.append(trade)
        return trade

    def equity(self, marks: dict[str, float]) -> float:
        eq = self.cash
        for symbol, pos in self.positions.items():
            price = marks.get(symbol, pos.entry_price)
            if pos.side == Side.LONG:
                eq += pos.size * price
            else:
                eq -= pos.size * price
        return eq
