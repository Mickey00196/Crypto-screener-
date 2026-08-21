from data.synthetic import generate_deterministic_trend, generate_synthetic_ohlcv
from engine.backtester import Backtester
from engine.costs import CostModel
from tests.test_engine.strategy_fixtures import (
    AlwaysShortStrategy,
    EMACrossStrategy,
    FixedRiskManager,
)


def _backtester(fee_bps=10.0, slippage_bps=5.0):
    return Backtester(
        cost_model=CostModel(taker_fee_bps=fee_bps, slippage_bps=slippage_bps),
        risk_manager=FixedRiskManager(size=1.0),
        initial_capital=10_000.0,
    )


def test_trend_strategy_profitable_in_constant_uptrend():
    # Deterministic (noise-free) uptrend: this is a sanity check on the
    # engine's execution/cost mechanics, not a strategy-quality claim — the
    # noisy regime generator (used for the Phase 4 pipeline smoke test) can
    # legitimately produce a losing realized path even in a "trend_up"
    # regime over a short window, since 1% per-bar noise can dominate a
    # 0.06%/bar drift; that's realistic market noise, not an engine bug.
    df = generate_deterministic_trend(n_bars=300, timeframe="1h", pct_per_bar=0.003, direction="up")
    backtester = _backtester(fee_bps=2.0, slippage_bps=1.0)
    result = backtester.run(df, EMACrossStrategy(fast=5, slow=20), symbol="BTC/USDT")
    assert result.final_equity > result.initial_capital
    # A strictly monotonic trend never reverses, so a correctly-behaving
    # trend strategy may hold one continuous position rather than round-trip
    # multiple trades — either shape is correct here.
    assert len(result.trades) > 0 or result.open_position is not None


def test_short_only_strategy_loses_in_constant_uptrend():
    df = generate_deterministic_trend(n_bars=300, timeframe="1h", pct_per_bar=0.003, direction="up")
    result = _backtester(fee_bps=2.0, slippage_bps=1.0).run(df, AlwaysShortStrategy(), symbol="BTC/USDT")
    assert result.final_equity < result.initial_capital


def test_zero_volatility_series_produces_zero_trades():
    df = generate_synthetic_ohlcv(n_bars=200, timeframe="1h", regime="zero_vol", seed=1)
    result = _backtester().run(df, EMACrossStrategy(fast=3, slow=8), symbol="BTC/USDT")
    assert len(result.trades) == 0
    # equity is untouched since no position was ever opened
    assert result.final_equity == result.initial_capital
