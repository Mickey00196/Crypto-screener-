"""THE ONLY MODULE IN THIS REPO ALLOWED TO READ THE HOLDOUT SPLIT.

guard/holdout_guard.py's check_caller() inspects the immediate caller's
filename and raises HoldoutBreachError unless it is literally
"final_evaluation.py" — so importing data.storage.load_split(..., "holdout")
from anywhere else in this codebase fails loudly (see
tests/test_guard/test_holdout_guard.py).

Run this exactly ONCE per candidate strategy that has already cleared every
gate on validation-level (train/val + walk-forward) evidence. Whatever comes
out is final: if it fails, that strategy is dead — do not tune it and
re-run. See RESULTS.md / FINDINGS.md for what this produced."""

from __future__ import annotations

from dataclasses import dataclass

from data.storage import load_split
from engine.backtester import Backtester
from engine.costs import CostModel
from engine.metrics import MetricsSummary, summarize
from engine.types import BacktestResult, RiskManagerLike
from evaluation.gates import GateReport, check_gates


@dataclass
class FinalEvaluationResult:
    symbol: str
    timeframe: str
    backtest_result: BacktestResult
    metrics: MetricsSummary
    gate_report: GateReport


def run_final_evaluation(
    strategy,
    symbol: str,
    timeframe: str,
    cost_model: CostModel,
    risk_manager: RiskManagerLike,
    periods_per_year: float,
    initial_capital: float = 10_000.0,
    walk_forward_windows_passed: int = 0,
    min_walk_forward_windows: int = 3,
    bull_expectancy: float | None = None,
    bear_expectancy: float | None = None,
    benchmark_sortino: float | None = None,
    data_dir=None,
    holdout_path=None,
) -> FinalEvaluationResult:
    kwargs = {}
    if data_dir is not None:
        kwargs["data_dir"] = data_dir
    if holdout_path is not None:
        kwargs["holdout_path"] = holdout_path

    df = load_split(symbol, timeframe, "holdout", **kwargs)  # the ONE legitimate call site in this repo

    backtester = Backtester(cost_model, risk_manager, initial_capital=initial_capital)
    result = backtester.run(df, strategy, symbol=symbol)
    metrics = summarize(result.trades, result.equity_curve, periods_per_year)
    gate_report = check_gates(
        metrics,
        walk_forward_windows_passed=walk_forward_windows_passed,
        min_walk_forward_windows=min_walk_forward_windows,
        bull_expectancy=bull_expectancy,
        bear_expectancy=bear_expectancy,
        benchmark_sortino=benchmark_sortino,
    )
    return FinalEvaluationResult(
        symbol=symbol, timeframe=timeframe, backtest_result=result, metrics=metrics, gate_report=gate_report
    )
