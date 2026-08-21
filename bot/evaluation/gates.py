"""Definition-of-Done gate checks. ALL must pass simultaneously — a strategy
that clears win rate but fails profit factor or drawdown is rejected and
that must be stated explicitly, per the hard rules."""

from __future__ import annotations

from dataclasses import dataclass

from engine.metrics import MetricsSummary


@dataclass
class GateResult:
    name: str
    passed: bool
    value: float
    threshold: float
    detail: str = ""


@dataclass
class GateReport:
    results: list[GateResult]

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.results)

    def failing(self) -> list[GateResult]:
        return [r for r in self.results if not r.passed]

    def summary_lines(self) -> list[str]:
        lines = []
        for r in self.results:
            mark = "PASS" if r.passed else "FAIL"
            lines.append(f"[{mark}] {r.name}: value={r.value:.4f} threshold={r.threshold:.4f} {r.detail}")
        return lines


def check_gates(
    metrics: MetricsSummary,
    walk_forward_windows_passed: int,
    min_walk_forward_windows: int = 3,
    bull_expectancy: float | None = None,
    bear_expectancy: float | None = None,
    benchmark_sortino: float | None = None,
) -> GateReport:
    results = [
        GateResult("win_rate", metrics.win_rate >= 0.55, metrics.win_rate, 0.55),
        GateResult("profit_factor", metrics.profit_factor >= 1.3, metrics.profit_factor, 1.3),
        GateResult("expectancy_positive", metrics.expectancy > 0, metrics.expectancy, 0.0),
        GateResult("max_drawdown", metrics.max_drawdown >= -0.20, metrics.max_drawdown, -0.20),
        GateResult("sortino", metrics.sortino >= 1.0, metrics.sortino, 1.0),
        GateResult("trade_count", metrics.trade_count >= 200, float(metrics.trade_count), 200.0),
        GateResult(
            "walk_forward_consistency",
            walk_forward_windows_passed >= min_walk_forward_windows,
            float(walk_forward_windows_passed),
            float(min_walk_forward_windows),
        ),
    ]
    if bull_expectancy is not None:
        results.append(GateResult("bull_regime_expectancy", bull_expectancy > 0, bull_expectancy, 0.0))
    if bear_expectancy is not None:
        results.append(GateResult("bear_regime_expectancy", bear_expectancy > 0, bear_expectancy, 0.0))
    if benchmark_sortino is not None:
        results.append(
            GateResult(
                "beats_buy_and_hold_risk_adjusted",
                metrics.sortino > benchmark_sortino,
                metrics.sortino,
                benchmark_sortino,
            )
        )
    return GateReport(results=results)


def check_overfit(train_value: float, val_value: float, max_degradation_pct: float = 30.0) -> bool:
    """Returns True if OVERFITTED (validation degraded > max_degradation_pct
    vs. train) and should be rejected without further tuning."""
    if train_value <= 0:
        return val_value <= 0
    degradation_pct = (train_value - val_value) / train_value * 100
    return degradation_pct > max_degradation_pct
