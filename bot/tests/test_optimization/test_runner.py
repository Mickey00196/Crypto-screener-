from data.synthetic import generate_synthetic_ohlcv
from engine.costs import CostModel
from optimization.runner import run_family_optimization
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


def test_run_family_optimization_produces_one_result_per_config_and_logs_them(tmp_path):
    train = {"BTC/USDT": generate_synthetic_ohlcv(n_bars=300, timeframe="1h", regime="mixed", seed=1)}
    val = {"BTC/USDT": generate_synthetic_ohlcv(n_bars=150, timeframe="1h", regime="mixed", seed=2)}
    cost_model = CostModel(taker_fee_bps=10.0, slippage_bps=5.0)
    log_path = tmp_path / "EXPERIMENTS.md"

    results = run_family_optimization(
        EMACrossStrategy,
        param_space={"fast": [3, 5, 8], "slow": [15, 20, 30]},
        n_configs=5,
        seed=1,
        train_datasets=train,
        val_datasets=val,
        cost_model=cost_model,
        risk_manager_factory=_risk_manager_factory,
        periods_per_year=24 * 365,
        experiments_log_path=log_path,
        tag="[UNIT TEST]",
    )

    assert len(results) == 5
    for r in results:
        assert r.verdict in {"CANDIDATE", "OVERFIT_REJECTED"}

    assert log_path.exists()
    content = log_path.read_text()
    assert content.count("[UNIT TEST]") == 5
    assert "EMACrossStrategy" in content


def test_run_family_optimization_respects_budget_cap(tmp_path):
    train = {"BTC/USDT": generate_synthetic_ohlcv(n_bars=200, timeframe="1h", seed=1)}
    val = {"BTC/USDT": generate_synthetic_ohlcv(n_bars=100, timeframe="1h", seed=2)}
    cost_model = CostModel(taker_fee_bps=10.0, slippage_bps=5.0)

    results = run_family_optimization(
        EMACrossStrategy,
        param_space={"fast": [3, 5], "slow": [15, 20]},  # only 4 possible combos
        n_configs=50,  # budget far exceeds the space
        seed=1,
        train_datasets=train,
        val_datasets=val,
        cost_model=cost_model,
        risk_manager_factory=_risk_manager_factory,
        periods_per_year=24 * 365,
        experiments_log_path=tmp_path / "EXPERIMENTS.md",
    )
    assert len(results) == 4  # capped at the full parameter space, not 50
