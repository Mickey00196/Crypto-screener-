"""Trade/equity-curve metrics: win rate, profit factor, expectancy, R:R,
Sortino, max drawdown, trade count. Used by evaluation/gates.py to check the
Definition of Done."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from engine.types import Trade


def win_rate(trades: list[Trade]) -> float:
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t.pnl > 0)
    return wins / len(trades)


def profit_factor(trades: list[Trade]) -> float:
    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = -sum(t.pnl for t in trades if t.pnl < 0)
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def expectancy(trades: list[Trade]) -> float:
    if not trades:
        return 0.0
    return sum(t.pnl for t in trades) / len(trades)


def avg_r_multiple(trades: list[Trade]) -> float:
    rs = [t.r_multiple for t in trades if t.r_multiple is not None]
    return float(np.mean(rs)) if rs else float("nan")


def avg_win_loss_ratio(trades: list[Trade]) -> float:
    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [-t.pnl for t in trades if t.pnl < 0]
    if not wins or not losses:
        return float("nan")
    return float(np.mean(wins) / np.mean(losses))


def max_drawdown(equity_curve: pd.Series) -> float:
    """Returns a negative fraction, e.g. -0.18 for an 18% drawdown."""
    if len(equity_curve) == 0:
        return 0.0
    running_max = equity_curve.cummax()
    dd = (equity_curve - running_max) / running_max
    return float(dd.min())


def sortino_ratio(returns: pd.Series, periods_per_year: float, risk_free_annual: float = 0.0) -> float:
    if len(returns) == 0:
        return 0.0
    excess = returns - risk_free_annual / periods_per_year
    downside = excess[excess < 0]
    downside_std = downside.std(ddof=0)
    if downside_std == 0 or np.isnan(downside_std):
        return float("inf") if excess.mean() > 0 else 0.0
    return float(excess.mean() / downside_std * np.sqrt(periods_per_year))


def trade_count(trades: list[Trade]) -> int:
    return len(trades)


@dataclass
class MetricsSummary:
    win_rate: float
    profit_factor: float
    expectancy: float
    avg_r_multiple: float
    avg_win_loss_ratio: float
    max_drawdown: float
    sortino: float
    trade_count: int


def summarize(trades: list[Trade], equity_curve: pd.DataFrame, periods_per_year: float) -> MetricsSummary:
    eq = equity_curve["equity"] if "equity" in equity_curve else equity_curve.iloc[:, 0]
    returns = eq.pct_change().dropna()
    return MetricsSummary(
        win_rate=win_rate(trades),
        profit_factor=profit_factor(trades),
        expectancy=expectancy(trades),
        avg_r_multiple=avg_r_multiple(trades),
        avg_win_loss_ratio=avg_win_loss_ratio(trades),
        max_drawdown=max_drawdown(eq),
        sortino=sortino_ratio(returns, periods_per_year),
        trade_count=trade_count(trades),
    )
