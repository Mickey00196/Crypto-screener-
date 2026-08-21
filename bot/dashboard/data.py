"""Pure data-shaping functions for the dashboard, kept separate from
dashboard/app.py's Streamlit calls so they are unit-testable without a
running Streamlit server."""

from __future__ import annotations

import pandas as pd

from live.state import TradingState

TRADE_LOG_COLUMNS = [
    "symbol",
    "side",
    "entry_time",
    "entry_price",
    "exit_time",
    "exit_price",
    "size",
    "pnl",
    "exit_reason",
]
POSITION_COLUMNS = ["symbol", "side", "size", "entry_price", "entry_time", "stop_price", "take_profit_price"]


def trade_log_dataframe(state: TradingState) -> pd.DataFrame:
    if not state.trade_log:
        return pd.DataFrame(columns=TRADE_LOG_COLUMNS)
    return pd.DataFrame(state.trade_log)


def equity_curve_dataframe(state: TradingState) -> pd.DataFrame:
    """Cumulative equity from initial_capital + realized trade P&L, one
    point per CLOSED trade. This does not mark open positions to a live
    price (the dashboard has no independent live feed) — open positions are
    shown separately in the positions table instead."""
    trades = trade_log_dataframe(state)
    if trades.empty:
        return pd.DataFrame({"trade_number": [0], "equity": [state.initial_capital]})
    trades = trades.sort_values("exit_time").reset_index(drop=True)
    equity = state.initial_capital + trades["pnl"].cumsum()
    return pd.DataFrame(
        {"trade_number": range(1, len(trades) + 1), "exit_time": trades["exit_time"], "equity": equity}
    )


def drawdown_dataframe(equity_df: pd.DataFrame) -> pd.DataFrame:
    running_max = equity_df["equity"].cummax()
    dd = (equity_df["equity"] - running_max) / running_max
    return equity_df.assign(drawdown=dd)


def open_positions_dataframe(state: TradingState) -> pd.DataFrame:
    if not state.positions:
        return pd.DataFrame(columns=POSITION_COLUMNS)
    rows = [
        {
            "symbol": p.symbol,
            "side": p.side,
            "size": p.size,
            "entry_price": p.entry_price,
            "entry_time": p.entry_time,
            "stop_price": p.stop_price,
            "take_profit_price": p.take_profit_price,
        }
        for p in state.positions.values()
    ]
    return pd.DataFrame(rows)
