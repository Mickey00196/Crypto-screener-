"""Run a single strategy+config through the engine on a given symbol/
timeframe/split. Never reads "holdout" (data/storage.py's guard blocks any
caller but evaluation/final_evaluation.py from that split anyway).

Run: python scripts/run_backtest.py
"""

from __future__ import annotations

import typer

from data.storage import load_split
from engine.backtester import Backtester
from engine.costs import CostModel
from engine.metrics import summarize
from risk.risk_manager import RiskConfig, RiskManager
from settings import load_settings
from strategies.trend_filtered_pullback import TrendFilteredPullbackStrategy

STRATEGY_REGISTRY = {
    "trend_filtered_pullback": TrendFilteredPullbackStrategy,
}


def main(
    strategy_name: str = "trend_filtered_pullback",
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    split: str = "train",
) -> None:
    if split == "holdout":
        raise typer.BadParameter(
            "this script is not evaluation/final_evaluation.py — it cannot read 'holdout' "
            "(guard/holdout_guard.py will reject it anyway)."
        )
    settings = load_settings()
    strategy_cls = STRATEGY_REGISTRY[strategy_name]
    strategy = strategy_cls()

    df = load_split(symbol, timeframe, split)
    cost_model = CostModel(
        taker_fee_bps=settings.costs.taker_fee_bps,
        slippage_bps=settings.costs.slippage_bps,
        funding_bps_per_8h=settings.costs.funding_bps_per_8h,
    )
    risk_manager = RiskManager(RiskConfig.from_settings(settings.risk))
    backtester = Backtester(cost_model, risk_manager, initial_capital=10_000.0)
    result = backtester.run(df, strategy, symbol=symbol)

    periods_per_year = {"5m": 288 * 365, "15m": 96 * 365, "1h": 24 * 365, "4h": 6 * 365}[timeframe]
    metrics = summarize(result.trades, result.equity_curve, periods_per_year)

    print(f"{strategy_name} on {symbol}/{timeframe} ({split}): {len(result.trades)} trades")
    print(f"  win_rate={metrics.win_rate:.3f} profit_factor={metrics.profit_factor:.3f}")
    print(f"  expectancy={metrics.expectancy:.4f} avg_r={metrics.avg_r_multiple:.3f}")
    print(f"  max_drawdown={metrics.max_drawdown:.3%} sortino={metrics.sortino:.3f}")
    print(f"  final_equity={result.final_equity:.2f} (started {result.initial_capital:.2f})")


if __name__ == "__main__":
    typer.run(main)
