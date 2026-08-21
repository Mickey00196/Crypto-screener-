from engine.metrics import MetricsSummary
from evaluation.gates import check_gates, check_overfit


def _passing_metrics():
    return MetricsSummary(
        win_rate=0.60,
        profit_factor=1.5,
        expectancy=10.0,
        avg_r_multiple=0.8,
        avg_win_loss_ratio=1.2,
        max_drawdown=-0.10,
        sortino=1.5,
        trade_count=250,
    )


def test_all_gates_pass_for_qualifying_metrics():
    report = check_gates(_passing_metrics(), walk_forward_windows_passed=3, min_walk_forward_windows=3)
    assert report.all_passed
    assert report.failing() == []


def test_win_rate_gate_fails_below_threshold():
    metrics = _passing_metrics()
    metrics.win_rate = 0.50
    report = check_gates(metrics, walk_forward_windows_passed=3)
    assert not report.all_passed
    failing_names = {r.name for r in report.failing()}
    assert "win_rate" in failing_names


def test_high_win_rate_alone_does_not_pass_if_profit_factor_or_drawdown_fail():
    """The brief's explicit example: 90% win rate with bad R:R must still be
    rejected on profit factor / drawdown, not accepted on win rate alone."""
    metrics = MetricsSummary(
        win_rate=0.90,
        profit_factor=0.9,  # small wins, huge rare losses -> below 1.3
        expectancy=-5.0,
        avg_r_multiple=-0.1,
        avg_win_loss_ratio=0.3,
        max_drawdown=-0.35,  # 35% drawdown, exceeds 20% gate
        sortino=0.2,
        trade_count=300,
    )
    report = check_gates(metrics, walk_forward_windows_passed=3)
    assert not report.all_passed
    failing_names = {r.name for r in report.failing()}
    assert "profit_factor" in failing_names
    assert "max_drawdown" in failing_names
    assert "expectancy_positive" in failing_names


def test_trade_count_gate():
    metrics = _passing_metrics()
    metrics.trade_count = 150
    report = check_gates(metrics, walk_forward_windows_passed=3)
    assert not report.all_passed


def test_walk_forward_consistency_gate_requires_minimum_windows():
    report = check_gates(_passing_metrics(), walk_forward_windows_passed=2, min_walk_forward_windows=3)
    assert not report.all_passed


def test_regime_gates_optional_but_enforced_when_provided():
    passing = check_gates(
        _passing_metrics(), walk_forward_windows_passed=3, bull_expectancy=5.0, bear_expectancy=2.0
    )
    assert passing.all_passed

    failing = check_gates(
        _passing_metrics(), walk_forward_windows_passed=3, bull_expectancy=5.0, bear_expectancy=-2.0
    )
    assert not failing.all_passed


def test_benchmark_gate():
    beats = check_gates(_passing_metrics(), walk_forward_windows_passed=3, benchmark_sortino=1.0)
    assert beats.all_passed  # sortino 1.5 > benchmark 1.0

    loses = check_gates(_passing_metrics(), walk_forward_windows_passed=3, benchmark_sortino=2.0)
    assert not loses.all_passed


def test_check_overfit_flags_large_degradation():
    assert check_overfit(train_value=10.0, val_value=5.0, max_degradation_pct=30.0) is True  # 50% degradation


def test_check_overfit_passes_small_degradation():
    # 20% degradation, below the 30% rejection threshold
    assert check_overfit(train_value=10.0, val_value=8.0, max_degradation_pct=30.0) is False


def test_check_overfit_handles_nonpositive_train():
    assert check_overfit(train_value=0.0, val_value=0.0) is True
    assert check_overfit(train_value=0.0, val_value=5.0) is False
