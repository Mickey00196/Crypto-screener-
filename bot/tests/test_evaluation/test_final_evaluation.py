from engine.costs import CostModel
from evaluation.final_evaluation import run_final_evaluation
from risk.risk_manager import RiskConfig, RiskManager
from tests.test_engine.strategy_fixtures import EMACrossStrategy


def test_final_evaluation_is_the_legitimate_holdout_caller(populated_store):
    """This is the ONE place in the whole test suite that successfully reads
    the holdout split — proving the guard allows the legitimate caller, not
    just that it blocks everyone else (see test_guard/test_holdout_guard.py
    for the rejection side)."""
    cost_model = CostModel(taker_fee_bps=25.0, slippage_bps=5.0)
    risk_manager = RiskManager(
        RiskConfig(
            max_risk_per_trade_pct=1.0,
            max_position_pct=20.0,
            max_concurrent_positions=3,
            daily_loss_limit_pct=3.0,
            max_drawdown_kill_switch_pct=15.0,
            atr_period=5,
        )
    )
    result = run_final_evaluation(
        EMACrossStrategy(fast=3, slow=8),
        populated_store["symbol"],
        populated_store["timeframe"],
        cost_model,
        risk_manager,
        periods_per_year=24 * 365,
        data_dir=populated_store["data_dir"],
        holdout_path=populated_store["holdout_path"],
    )
    assert result.symbol == populated_store["symbol"]
    assert result.backtest_result is not None
    assert result.metrics is not None
    assert result.gate_report is not None
    # gates almost certainly fail on this tiny synthetic slice (few trades) —
    # that is fine and expected; the point of this test is that the read
    # itself succeeded, not that the strategy passed.
    assert isinstance(result.gate_report.all_passed, bool)
