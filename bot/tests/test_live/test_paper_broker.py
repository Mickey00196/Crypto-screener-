import pandas as pd
import pytest

from engine.costs import CostModel
from engine.types import Side
from live.paper_broker import PaperBroker
from live.state import TradingState


def _bar(open_price=100.0, ts="2024-01-01T00:00:00Z"):
    return pd.Series(
        {"timestamp": ts, "open": open_price, "high": open_price, "low": open_price, "close": open_price}
    )


def test_open_position_applies_slippage_and_fee_like_the_backtest_cost_model():
    cost_model = CostModel(taker_fee_bps=10.0, slippage_bps=10.0)  # 0.1% fee, 0.1% slippage
    broker = PaperBroker(cost_model)
    state = TradingState(trading_mode="paper", cash=10_000.0, initial_capital=10_000.0)

    fill = broker.open_position(state, "BTC/EUR", Side.LONG, size=0.1, bar=_bar(open_price=40_000.0))

    expected_actual_price = 40_000.0 * 1.001  # adverse slippage on a long entry
    assert fill.intended_price == 40_000.0
    assert fill.actual_price == pytest.approx(expected_actual_price)
    expected_notional = expected_actual_price * 0.1
    expected_fee = expected_notional * 0.001
    assert fill.fee == pytest.approx(expected_fee)
    assert state.cash == pytest.approx(10_000.0 - expected_notional - expected_fee)
    assert "BTC/EUR" in state.positions
    assert state.positions["BTC/EUR"].entry_price == pytest.approx(expected_actual_price)


def test_close_position_records_trade_log_entry_and_removes_position():
    cost_model = CostModel(taker_fee_bps=0.0, slippage_bps=0.0)  # isolate P&L arithmetic from costs
    broker = PaperBroker(cost_model)
    state = TradingState(trading_mode="paper", cash=10_000.0, initial_capital=10_000.0)

    broker.open_position(state, "BTC/EUR", Side.LONG, size=1.0, bar=_bar(open_price=100.0))
    broker.close_position(state, "BTC/EUR", bar=_bar(open_price=110.0), reason="signal")

    assert "BTC/EUR" not in state.positions
    assert len(state.trade_log) == 1
    trade = state.trade_log[0]
    assert trade["pnl"] == pytest.approx(10.0)  # (110-100)*1.0, zero costs
    assert trade["exit_reason"] == "signal"
    assert state.cash == pytest.approx(10_000.0 + 10.0)  # started flat at 10000, net +10 pnl


def test_short_position_pnl_direction():
    cost_model = CostModel(taker_fee_bps=0.0, slippage_bps=0.0)
    broker = PaperBroker(cost_model)
    state = TradingState(trading_mode="paper", cash=10_000.0, initial_capital=10_000.0)

    broker.open_position(state, "BTC/EUR", Side.SHORT, size=1.0, bar=_bar(open_price=100.0))
    broker.close_position(state, "BTC/EUR", bar=_bar(open_price=90.0), reason="signal")

    trade = state.trade_log[0]
    assert trade["pnl"] == pytest.approx(10.0)  # price fell 10, short profits 10
