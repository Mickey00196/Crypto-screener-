"""Train-fit / validation-select optimization loop with an anti-overfit
budget. Every single run appends one row to EXPERIMENTS.md — hypothesis
(params), in-sample (train) result, validation result, verdict, lesson
learned — per the brief's Phase 4 requirement. Fits and tunes on train only;
selects on validation only; never touches holdout (evaluation/
final_evaluation.py is the only module allowed to)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from engine.costs import CostModel
from engine.metrics import MetricsSummary
from engine.types import RiskManagerLike
from evaluation.aggregate import evaluate_strategy
from evaluation.gates import check_overfit
from optimization.grid import sample_configs

EXPERIMENTS_HEADER = (
    "| tag | family | config_id | params | train_win_rate | train_pf | "
    "val_win_rate | val_pf | verdict | lesson |\n"
    "|---|---|---|---|---|---|---|---|---|---|\n"
)


@dataclass
class OptimizationRunResult:
    config_id: int
    params: dict
    train_metrics: MetricsSummary
    val_metrics: MetricsSummary
    verdict: str
    lesson: str = ""


def ensure_experiments_file(path: Path) -> None:
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Experiment Log\n\n" + EXPERIMENTS_HEADER)


def append_experiment_row(
    path: Path,
    tag: str,
    family: str,
    config_id: int,
    params: dict,
    train: MetricsSummary,
    val: MetricsSummary,
    verdict: str,
    lesson: str = "",
) -> None:
    ensure_experiments_file(path)
    row = (
        f"| {tag} | {family} | {config_id} | `{params}` | "
        f"{train.win_rate:.3f} | {train.profit_factor:.3f} | "
        f"{val.win_rate:.3f} | {val.profit_factor:.3f} | {verdict} | {lesson} |\n"
    )
    with open(path, "a") as f:
        f.write(row)


def run_family_optimization(
    strategy_cls: Callable[..., Any],
    param_space: dict[str, list],
    n_configs: int,
    seed: int,
    train_datasets: dict[str, pd.DataFrame],
    val_datasets: dict[str, pd.DataFrame],
    cost_model: CostModel,
    risk_manager_factory: Callable[[], RiskManagerLike],
    periods_per_year: float,
    experiments_log_path: Path,
    tag: str = "",
    overfit_metric: str = "expectancy",
    overfit_max_degradation_pct: float = 30.0,
) -> list[OptimizationRunResult]:
    """Runs up to n_configs sampled configs (the anti-overfit budget — log
    the count, and when it's spent the family is done). Returns every run's
    result, including OVERFIT_REJECTED ones, so callers can see the full
    picture; only non-rejected CANDIDATE results should proceed to
    walk-forward/gate checks."""
    configs = sample_configs(param_space, n_configs, seed)
    results = []

    for config_id, params in enumerate(configs):
        strategy = strategy_cls(**params)
        train_agg = evaluate_strategy(
            strategy, train_datasets, cost_model, risk_manager_factory, periods_per_year
        )
        val_agg = evaluate_strategy(
            strategy, val_datasets, cost_model, risk_manager_factory, periods_per_year
        )

        train_value = getattr(train_agg.pooled_metrics, overfit_metric)
        val_value = getattr(val_agg.pooled_metrics, overfit_metric)
        overfitted = check_overfit(train_value, val_value, overfit_max_degradation_pct)
        verdict = "OVERFIT_REJECTED" if overfitted else "CANDIDATE"
        lesson = (
            f"train {overfit_metric}={train_value:.4f} -> val {overfit_metric}={val_value:.4f}: "
            + ("degraded >30%, rejected without re-tuning" if overfitted else "held up within budget")
        )

        result = OptimizationRunResult(
            config_id=config_id,
            params=params,
            train_metrics=train_agg.pooled_metrics,
            val_metrics=val_agg.pooled_metrics,
            verdict=verdict,
            lesson=lesson,
        )
        results.append(result)
        append_experiment_row(
            experiments_log_path,
            tag,
            strategy_cls.__name__,
            config_id,
            params,
            train_agg.pooled_metrics,
            val_agg.pooled_metrics,
            verdict,
            lesson,
        )

    return results
