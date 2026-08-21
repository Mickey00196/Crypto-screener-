"""Runs a strategy across multiple (symbol,timeframe) datasets and pools the
resulting trades into one combined MetricsSummary. Shared by the
optimization loop (train/val) and evaluation/final_evaluation.py (holdout)
so both use identical evaluation logic."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from engine.backtester import Backtester
from engine.costs import CostModel
from engine.metrics import (
    MetricsSummary,
    avg_r_multiple,
    avg_win_loss_ratio,
    expectancy,
    max_drawdown,
    profit_factor,
    sortino_ratio,
    trade_count,
    win_rate,
)
from engine.types import BacktestResult, RiskManagerLike


@dataclass
class AggregateResult:
    per_dataset: dict[str, BacktestResult]
    pooled_metrics: MetricsSummary


def evaluate_strategy(
    strategy,
    datasets: dict[str, pd.DataFrame],
    cost_model: CostModel,
    risk_manager_factory: Callable[[], RiskManagerLike],
    periods_per_year: float,
    initial_capital: float = 10_000.0,
) -> AggregateResult:
    """risk_manager_factory is called once PER DATASET (a fresh instance
    each time) so stateful daily-loss tracking never leaks across an
    unrelated symbol/timeframe."""
    per_dataset: dict[str, BacktestResult] = {}
    all_trades = []
    drawdowns = []
    sortinos = []

    for key, df in datasets.items():
        risk_manager = risk_manager_factory()
        backtester = Backtester(cost_model, risk_manager, initial_capital=initial_capital)
        result = backtester.run(df, strategy, symbol=key)
        per_dataset[key] = result
        all_trades.extend(result.trades)

        eq = result.equity_curve["equity"]
        drawdowns.append(max_drawdown(eq))
        returns = eq.pct_change().dropna()
        sortinos.append(sortino_ratio(returns, periods_per_year))

    pooled_metrics = MetricsSummary(
        win_rate=win_rate(all_trades),
        profit_factor=profit_factor(all_trades),
        expectancy=expectancy(all_trades),
        avg_r_multiple=avg_r_multiple(all_trades),
        avg_win_loss_ratio=avg_win_loss_ratio(all_trades),
        max_drawdown=min(drawdowns) if drawdowns else 0.0,  # worst (most negative) across datasets
        sortino=(sum(sortinos) / len(sortinos)) if sortinos else 0.0,
        trade_count=trade_count(all_trades),
    )
    return AggregateResult(per_dataset=per_dataset, pooled_metrics=pooled_metrics)
