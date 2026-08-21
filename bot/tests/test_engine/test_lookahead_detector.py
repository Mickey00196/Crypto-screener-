import pytest

from data.synthetic import generate_synthetic_ohlcv
from engine.backtester import Backtester
from engine.costs import CostModel
from engine.lookahead_check import LookaheadError, detect_lookahead
from tests.test_engine.strategy_fixtures import (
    EMACrossStrategy,
    FixedRiskManager,
    LookaheadBuggyStrategy,
)


def test_clean_strategy_passes_lookahead_check():
    df = generate_synthetic_ohlcv(n_bars=300, timeframe="1h", regime="mixed", seed=2)
    report = detect_lookahead(EMACrossStrategy(fast=3, slow=8), df)
    assert report.passed


def test_buggy_strategy_is_caught_by_lookahead_check():
    """The brief's explicit requirement: the detector must FAIL (raise) when
    a lookahead bug is deliberately introduced — proving the detector works,
    not just that clean strategies pass it."""
    df = generate_synthetic_ohlcv(n_bars=300, timeframe="1h", regime="mixed", seed=2)
    with pytest.raises(LookaheadError) as exc_info:
        detect_lookahead(LookaheadBuggyStrategy(), df)
    assert "bar index" in str(exc_info.value)


def test_fills_execute_at_next_bar_open_not_same_bar_close():
    df = generate_synthetic_ohlcv(n_bars=300, timeframe="1h", regime="mixed", seed=2)
    backtester = Backtester(
        cost_model=CostModel(taker_fee_bps=10.0, slippage_bps=0.0),
        risk_manager=FixedRiskManager(size=1.0),
        initial_capital=10_000.0,
    )
    result = backtester.run(df, EMACrossStrategy(fast=3, slow=8), symbol="BTC/USDT")
    assert len(result.trades) > 0

    ts_to_open = dict(zip(df["timestamp"], df["open"], strict=True))
    for trade in result.trades:
        assert trade.entry_time in ts_to_open
        # zero slippage configured => fill must equal that bar's OPEN exactly,
        # never its close (which is what the signal was computed from).
        assert trade.entry_price == pytest.approx(ts_to_open[trade.entry_time], abs=1e-9)
