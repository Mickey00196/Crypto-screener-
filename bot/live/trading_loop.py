"""Scheduled trading loop: on each newly-closed bar, compute the strategy
signal, apply risk management, and route through paper_broker (default) or
live_broker (ONLY if TRADING_MODE=live). Sleeps until the next timeframe-
aligned bar close between iterations.

Execution timing mirrors the backtest exactly: the signal is computed from
`closed_df` (bars whose close has already happened), and the resulting order
is filled at the OPEN of the bar that is still forming when the signal was
computed — i.e. df.iloc[-1] (the same next-bar-open convention
engine/backtester.py uses), never the bar the signal itself was computed
from.

fetch_latest_bars (network I/O) is deliberately separated from
process_latest_closed_bar (pure logic) so the latter is fully unit-testable
without live exchange access."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from data.fetch_bitvavo import fetch_bitvavo_ohlcv, make_bitvavo_exchange
from engine.costs import CostModel
from engine.types import RiskManagerLike, Side
from live.live_broker import LiveBroker
from live.paper_broker import PaperBroker
from live.state import load_state, save_state

TIMEFRAME_SECONDS = {"5m": 300, "15m": 900, "1h": 3600, "4h": 14400}


class TradingLoop:
    def __init__(
        self,
        strategy,
        risk_manager: RiskManagerLike,
        symbol: str,
        timeframe: str,
        cost_model: CostModel,
        state_path: str | Path,
        lookback_bars: int = 300,
        trading_mode: str | None = None,
    ):
        if timeframe not in TIMEFRAME_SECONDS:
            raise ValueError(f"unsupported timeframe {timeframe!r}")
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.symbol = symbol
        self.timeframe = timeframe
        self.cost_model = cost_model
        self.state_path = state_path
        self.lookback_bars = lookback_bars
        self.trading_mode = trading_mode or os.environ.get("TRADING_MODE", "paper")
        self.paper_broker = PaperBroker(cost_model)
        self.live_broker = LiveBroker.from_env() if self.trading_mode == "live" else None
        self.state = load_state(state_path, trading_mode=self.trading_mode)

    def seconds_until_next_bar_close(self, now: datetime | None = None) -> float:
        now = now or datetime.now(UTC)
        tf_seconds = TIMEFRAME_SECONDS[self.timeframe]
        epoch_seconds = now.timestamp()
        next_close = (int(epoch_seconds // tf_seconds) + 1) * tf_seconds
        return max(next_close - epoch_seconds, 1.0)

    @retry(wait=wait_exponential(multiplier=1, min=2, max=60), stop=stop_after_attempt(5))
    def fetch_latest_bars(self) -> pd.DataFrame:
        since = datetime.now(UTC) - timedelta(seconds=TIMEFRAME_SECONDS[self.timeframe] * self.lookback_bars)
        exchange = make_bitvavo_exchange()
        return fetch_bitvavo_ohlcv(self.symbol, self.timeframe, since, exchange=exchange)

    def process_latest_closed_bar(self, df: pd.DataFrame) -> None:
        """df's last row is the still-forming current bar; everything before
        it is closed. Idempotent: re-processing the same closed bar (e.g.
        after a restart) is a no-op, checked via state.last_processed_bar_time."""
        if len(df) < 2:
            return
        closed_df = df.iloc[:-1].reset_index(drop=True)
        execution_bar = df.iloc[-1]
        latest_closed_ts = str(closed_df["timestamp"].iloc[-1])

        if self.state.last_processed_bar_time.get(self.symbol) == latest_closed_ts:
            return

        signals = self.strategy.generate_signals(closed_df)
        desired = int(signals.iloc[-1])
        current_pos = self.state.positions.get(self.symbol)
        current_direction = 0 if current_pos is None else (1 if current_pos.side == "long" else -1)

        if desired != current_direction:
            if current_pos is not None:
                self._route_close(execution_bar, reason="signal")
            if desired != 0:
                side = Side.LONG if desired == 1 else Side.SHORT
                equity = self._current_equity(execution_bar)
                decision = self.risk_manager.decide(side, self.symbol, closed_df, equity, {})
                if decision.size > 0:
                    self._route_open(execution_bar, side, decision)

        self.state.last_processed_bar_time[self.symbol] = latest_closed_ts
        save_state(self.state, self.state_path)

    def _current_equity(self, bar: pd.Series) -> float:
        eq = self.state.cash
        pos = self.state.positions.get(self.symbol)
        if pos is not None:
            mark = float(bar["close"])
            eq += pos.size * mark if pos.side == "long" else -pos.size * mark
        return eq

    def _route_open(self, bar: pd.Series, side: Side, decision) -> None:
        if self.trading_mode == "live":
            self.live_broker.place_market_order(self.symbol, side, decision.size)
        self.paper_broker.open_position(
            self.state, self.symbol, side, decision.size, bar, decision.stop_price, decision.take_profit_price
        )

    def _route_close(self, bar: pd.Series, reason: str) -> None:
        if self.trading_mode == "live":
            pos = self.state.positions[self.symbol]
            close_side = Side.SHORT if pos.side == "long" else Side.LONG
            self.live_broker.place_market_order(self.symbol, close_side, pos.size)
        self.paper_broker.close_position(self.state, self.symbol, bar, reason)

    async def run_forever(self) -> None:
        import asyncio

        while True:
            await asyncio.sleep(self.seconds_until_next_bar_close())
            df = self.fetch_latest_bars()
            self.process_latest_closed_bar(df)
