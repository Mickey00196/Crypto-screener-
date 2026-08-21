import pytest

from dashboard.data import (
    drawdown_dataframe,
    equity_curve_dataframe,
    open_positions_dataframe,
    trade_log_dataframe,
)
from live.state import OpenPositionState, TradingState


def _state_with_trades():
    state = TradingState(trading_mode="paper", cash=10_100.0, initial_capital=10_000.0)
    state.trade_log = [
        {"symbol": "BTC/EUR", "exit_time": "2024-01-01T02:00:00Z", "pnl": 50.0},
        {"symbol": "BTC/EUR", "exit_time": "2024-01-01T01:00:00Z", "pnl": -30.0},  # out of order on purpose
        {"symbol": "BTC/EUR", "exit_time": "2024-01-01T03:00:00Z", "pnl": 80.0},
    ]
    return state


def test_trade_log_dataframe_empty_has_expected_columns():
    state = TradingState(trading_mode="paper", cash=10_000.0, initial_capital=10_000.0)
    df = trade_log_dataframe(state)
    assert df.empty
    assert "pnl" in df.columns


def test_equity_curve_orders_by_exit_time_and_accumulates_pnl():
    state = _state_with_trades()
    equity_df = equity_curve_dataframe(state)
    assert list(equity_df["equity"]) == [
        pytest.approx(10_000.0 - 30.0),
        pytest.approx(10_000.0 - 30.0 + 50.0),
        pytest.approx(10_000.0 - 30.0 + 50.0 + 80.0),
    ]


def test_equity_curve_with_no_trades_is_flat_at_initial_capital():
    state = TradingState(trading_mode="paper", cash=10_000.0, initial_capital=10_000.0)
    equity_df = equity_curve_dataframe(state)
    assert list(equity_df["equity"]) == [10_000.0]


def test_drawdown_dataframe_computes_negative_fraction_from_peak():
    state = _state_with_trades()
    equity_df = equity_curve_dataframe(state)
    dd_df = drawdown_dataframe(equity_df)
    assert dd_df["drawdown"].max() == pytest.approx(0.0)  # peak has zero drawdown
    assert (dd_df["drawdown"] <= 0).all()


def test_open_positions_dataframe_reflects_state():
    state = TradingState(trading_mode="paper", cash=9000.0, initial_capital=10_000.0)
    state.positions["ETH/EUR"] = OpenPositionState(
        symbol="ETH/EUR", side="long", size=1.5, entry_price=2000.0, entry_time="2024-01-01T00:00:00Z"
    )
    df = open_positions_dataframe(state)
    assert len(df) == 1
    assert df.iloc[0]["symbol"] == "ETH/EUR"
    assert df.iloc[0]["entry_price"] == 2000.0


def test_open_positions_dataframe_empty_has_expected_columns():
    state = TradingState(trading_mode="paper", cash=10_000.0, initial_capital=10_000.0)
    df = open_positions_dataframe(state)
    assert df.empty
    assert "symbol" in df.columns
