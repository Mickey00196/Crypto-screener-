"""Streamlit dashboard: equity curve, drawdown, trade log, live/paper
positions. Reads live/trading_loop.py's persisted state (JSON) — works
against real paper-trading state once scripts/run_paper_trading.py has been
run, or against any state.json produced by the test suite / a manual demo.

Run: streamlit run dashboard/app.py
Env: TRADING_STATE_PATH overrides the default live/paper_state.json path.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from dashboard.data import (
    drawdown_dataframe,
    equity_curve_dataframe,
    open_positions_dataframe,
    trade_log_dataframe,
)
from live.state import load_state

BOT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_PATH = BOT_ROOT / "live" / "paper_state.json"

st.set_page_config(page_title="Crypto Trading Bot", layout="wide")
st.title("Crypto Trading Bot — Paper/Live Dashboard")

state_path = Path(os.environ.get("TRADING_STATE_PATH", DEFAULT_STATE_PATH))
if not state_path.exists():
    st.warning(
        f"No trading state found at `{state_path}`. Start the paper-trading loop "
        "(`python scripts/run_paper_trading.py`) to populate it, or point "
        "`TRADING_STATE_PATH` at an existing state file."
    )
    st.stop()

state = load_state(state_path)
st.caption(f"Mode: **{state.trading_mode}** — state file: `{state_path}`")

trades_df = trade_log_dataframe(state)
equity_df = equity_curve_dataframe(state)
current_equity = equity_df["equity"].iloc[-1] if not equity_df.empty else state.initial_capital

col1, col2, col3 = st.columns(3)
col1.metric("Current Equity (realized)", f"{current_equity:,.2f}")
col2.metric("Closed Trades", len(trades_df))
col3.metric("Open Positions", len(state.positions))

st.subheader("Equity Curve")
if len(equity_df) > 1:
    st.line_chart(equity_df.set_index("trade_number")["equity"])
else:
    st.info("Not enough closed trades yet to plot an equity curve.")

st.subheader("Drawdown")
dd_df = drawdown_dataframe(equity_df)
if len(dd_df) > 1:
    st.area_chart(dd_df.set_index("trade_number")["drawdown"])
else:
    st.info("Not enough closed trades yet to plot drawdown.")

st.subheader("Open Positions")
st.dataframe(open_positions_dataframe(state), width="stretch")

st.subheader("Trade Log")
st.dataframe(trades_df, width="stretch")
