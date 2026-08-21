from data.synthetic import generate_synthetic_ohlcv
from engine.costs import CostModel
from evaluation.aggregate import evaluate_strategy
from risk.risk_manager import RiskConfig, RiskManager
from tests.test_engine.strategy_fixtures import EMACrossStrategy


def _risk_manager_factory():
    return RiskManager(
        RiskConfig(
            max_risk_per_trade_pct=1.0,
            max_position_pct=20.0,
            max_concurrent_positions=3,
            daily_loss_limit_pct=3.0,
            max_drawdown_kill_switch_pct=15.0,
            atr_period=5,
        )
    )


def test_evaluate_strategy_pools_trades_across_datasets():
    datasets = {
        "BTC/USDT": generate_synthetic_ohlcv(n_bars=300, timeframe="1h", regime="mixed", seed=1),
        "ETH/USDT": generate_synthetic_ohlcv(n_bars=300, timeframe="1h", regime="mixed", seed=2),
    }
    cost_model = CostModel(taker_fee_bps=10.0, slippage_bps=5.0)
    result = evaluate_strategy(
        EMACrossStrategy(fast=5, slow=20),
        datasets,
        cost_model,
        _risk_manager_factory,
        periods_per_year=24 * 365,
    )
    assert set(result.per_dataset.keys()) == {"BTC/USDT", "ETH/USDT"}
    total_trades = sum(len(r.trades) for r in result.per_dataset.values())
    assert result.pooled_metrics.trade_count == total_trades


def test_evaluate_strategy_risk_manager_state_does_not_leak_across_datasets():
    """Each dataset must get a FRESH risk manager instance — otherwise
    stateful daily-loss tracking from one symbol would incorrectly block
    trading on an unrelated symbol."""
    datasets = {
        "BTC/USDT": generate_synthetic_ohlcv(n_bars=200, timeframe="1h", regime="trend_down", seed=3),
        "ETH/USDT": generate_synthetic_ohlcv(n_bars=200, timeframe="1h", regime="trend_up", seed=4),
    }
    cost_model = CostModel(taker_fee_bps=10.0, slippage_bps=5.0)
    seen_instances = []

    def tracking_factory():
        rm = _risk_manager_factory()
        seen_instances.append(rm)
        return rm

    evaluate_strategy(
        EMACrossStrategy(fast=5, slow=20), datasets, cost_model, tracking_factory, periods_per_year=24 * 365
    )
    assert len(seen_instances) == len(datasets)
    assert len(set(id(rm) for rm in seen_instances)) == len(datasets)  # all distinct instances
