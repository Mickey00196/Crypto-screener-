import pytest

from data.synthetic import generate_synthetic_ohlcv
from engine.lookahead_check import detect_lookahead
from strategies.trend_continuation_confluence import TrendContinuationConfluenceStrategy
from strategies.trend_filtered_pullback import TrendFilteredPullbackStrategy
from strategies.volatility_breakout_trend import VolatilityBreakoutTrendStrategy

ALL_STRATEGIES = [
    TrendFilteredPullbackStrategy(ema_period=20, adx_period=5, rsi_period=5),
    VolatilityBreakoutTrendStrategy(donchian_period=10, st_period=5, obv_lookback=3),
    TrendContinuationConfluenceStrategy(ema_fast=5, ema_slow=15, macd_fast=5, macd_slow=10, rsi_period=5),
]


@pytest.fixture(scope="module")
def synthetic_df():
    return generate_synthetic_ohlcv(n_bars=400, timeframe="1h", regime="mixed", seed=11)


@pytest.mark.parametrize("strategy", ALL_STRATEGIES, ids=lambda s: type(s).__name__)
def test_strategy_has_params_dict(strategy):
    assert isinstance(strategy.params, dict)
    assert len(strategy.params) > 0


@pytest.mark.parametrize("strategy", ALL_STRATEGIES, ids=lambda s: type(s).__name__)
def test_signals_aligned_and_valid_values(strategy, synthetic_df):
    signals = strategy.generate_signals(synthetic_df)
    assert len(signals) == len(synthetic_df)
    assert set(signals.unique()).issubset({-1, 0, 1})


@pytest.mark.parametrize("strategy", ALL_STRATEGIES, ids=lambda s: type(s).__name__)
def test_strategy_passes_lookahead_check(strategy, synthetic_df):
    """Every strategy that will run in Phase 4's optimization loop must pass
    this check — it is the automated proof the hard rule requires."""
    report = detect_lookahead(strategy, synthetic_df, warmup=50)
    assert report.passed
