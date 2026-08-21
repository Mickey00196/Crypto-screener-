"""Event-driven, bar-by-bar backtest engine — the foundation every reported
number in this repo depends on.

Execution timing (the hard "no lookahead" rule, enforced structurally, not
just by convention): a strategy's signal for bar t is computed using
`generate_signals` over data through bar t's close. That signal is queued as
`pending_signal` and only executed using bar t+1's OPEN price, in the next
loop iteration — never bar t's own close or bar t+1's close/high/low. Stop-
loss/take-profit fills, by contrast, ARE checked against the current bar's
high/low while a position is open: that models a resting stop/limit order
actually sitting in the market, not the strategy peeking ahead.
"""

from __future__ import annotations

import pandas as pd

from engine.costs import CostModel
from engine.portfolio import Portfolio
from engine.types import BacktestResult, RiskManagerLike, Side


class Backtester:
    def __init__(
        self, cost_model: CostModel, risk_manager: RiskManagerLike, initial_capital: float = 10_000.0
    ):
        self.cost_model = cost_model
        self.risk_manager = risk_manager
        self.initial_capital = initial_capital

    def run(self, df: pd.DataFrame, strategy, symbol: str = "SYMBOL") -> BacktestResult:
        if df.empty:
            raise ValueError("cannot backtest an empty dataframe")
        df = df.reset_index(drop=True)
        signals = strategy.generate_signals(df)
        if len(signals) != len(df):
            raise ValueError("strategy.generate_signals must return a series the same length as df")
        signals = signals.reset_index(drop=True)

        portfolio = Portfolio(self.initial_capital)
        equity_history: list[float] = []
        equity_curve_rows: list[dict] = []
        pending_signal: int | None = None
        halted = False

        n = len(df)
        for i in range(n):
            bar = df.iloc[i]

            # 1. Execute any order queued from the previous bar's close, at THIS bar's open.
            if pending_signal is not None and not halted:
                self._execute_transition(portfolio, symbol, pending_signal, bar, df.iloc[: i + 1])
                pending_signal = None

            # 2. Manage an open position: stop-loss / take-profit checked against this bar's high/low.
            if symbol in portfolio.positions:
                self._check_stop_take_profit(portfolio, symbol, bar)

            # 3. Kill-switch check (risk manager's call, based on equity history so far).
            if not halted and self.risk_manager.should_halt(equity_history, self.initial_capital):
                halted = True
                if symbol in portfolio.positions:
                    self._force_close(portfolio, symbol, bar, reason="kill_switch")

            # 4. Mark to market.
            equity_now = portfolio.equity({symbol: bar["close"]})
            equity_history.append(equity_now)
            equity_curve_rows.append({"timestamp": bar["timestamp"], "equity": equity_now})

            # 5. Compute the desired position from THIS bar's close; queue for next bar's open.
            if not halted and i < n - 1:
                desired = int(signals.iloc[i])
                current = self._current_direction(portfolio, symbol)
                if desired != current:
                    pending_signal = desired

        equity_curve = pd.DataFrame(equity_curve_rows)
        final_equity = equity_curve_rows[-1]["equity"] if equity_curve_rows else self.initial_capital
        return BacktestResult(
            trades=portfolio.trades,
            equity_curve=equity_curve,
            initial_capital=self.initial_capital,
            final_equity=final_equity,
            open_position=portfolio.positions.get(symbol),
        )

    @staticmethod
    def _current_direction(portfolio: Portfolio, symbol: str) -> int:
        pos = portfolio.positions.get(symbol)
        if pos is None:
            return 0
        return 1 if pos.side == Side.LONG else -1

    def _execute_transition(
        self, portfolio: Portfolio, symbol: str, desired: int, bar: pd.Series, df_so_far: pd.DataFrame
    ) -> None:
        current_pos = portfolio.positions.get(symbol)
        if current_pos is not None:
            exit_price = self.cost_model.exit_fill_price(bar["open"], current_pos.side)
            fee = self.cost_model.fee(exit_price * current_pos.size)
            portfolio.close_position(symbol, exit_price, bar["timestamp"], fee, exit_reason="signal")

        if desired == 0:
            return

        side = Side.LONG if desired == 1 else Side.SHORT
        equity = portfolio.equity({symbol: bar["open"]})
        decision = self.risk_manager.decide(side, symbol, df_so_far, equity, portfolio.positions)
        if decision.size <= 0:
            return

        entry_price = self.cost_model.entry_fill_price(bar["open"], side)
        fee = self.cost_model.fee(entry_price * decision.size)
        portfolio.open_position(
            symbol,
            side,
            decision.size,
            entry_price,
            bar["timestamp"],
            fee,
            decision.stop_price,
            decision.take_profit_price,
        )

    def _check_stop_take_profit(self, portfolio: Portfolio, symbol: str, bar: pd.Series) -> None:
        pos = portfolio.positions[symbol]
        hit_price = None
        reason = None
        if pos.side == Side.LONG:
            if pos.stop_price is not None and bar["low"] <= pos.stop_price:
                hit_price, reason = pos.stop_price, "stop_loss"
            elif pos.take_profit_price is not None and bar["high"] >= pos.take_profit_price:
                hit_price, reason = pos.take_profit_price, "take_profit"
        else:
            if pos.stop_price is not None and bar["high"] >= pos.stop_price:
                hit_price, reason = pos.stop_price, "stop_loss"
            elif pos.take_profit_price is not None and bar["low"] <= pos.take_profit_price:
                hit_price, reason = pos.take_profit_price, "take_profit"

        if hit_price is not None:
            exit_price = self.cost_model.exit_fill_price(hit_price, pos.side)
            fee = self.cost_model.fee(exit_price * pos.size)
            portfolio.close_position(symbol, exit_price, bar["timestamp"], fee, exit_reason=reason)

    def _force_close(self, portfolio: Portfolio, symbol: str, bar: pd.Series, reason: str) -> None:
        pos = portfolio.positions[symbol]
        exit_price = self.cost_model.exit_fill_price(bar["close"], pos.side)
        fee = self.cost_model.fee(exit_price * pos.size)
        portfolio.close_position(symbol, exit_price, bar["timestamp"], fee, exit_reason=reason)
