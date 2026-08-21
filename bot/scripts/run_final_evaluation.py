"""Thin CLI wrapper around evaluation/final_evaluation.py — the ONE-SHOT,
ONE-TIME holdout evaluation. Run this exactly once per candidate strategy
that has already cleared every gate on validation-level evidence. Whatever
comes out is final; a failure kills that strategy, no re-tuning.

Run: python scripts/run_final_evaluation.py --family trend_filtered_pullback
"""

from __future__ import annotations

import json

import typer

from engine.costs import CostModel
from evaluation.final_evaluation import run_final_evaluation
from risk.risk_manager import RiskConfig, RiskManager
from settings import load_settings
from strategies.trend_continuation_confluence import TrendContinuationConfluenceStrategy
from strategies.trend_filtered_pullback import TrendFilteredPullbackStrategy
from strategies.volatility_breakout_trend import VolatilityBreakoutTrendStrategy

STRATEGY_REGISTRY = {
    "trend_filtered_pullback": TrendFilteredPullbackStrategy,
    "volatility_breakout_trend": VolatilityBreakoutTrendStrategy,
    "trend_continuation_confluence": TrendContinuationConfluenceStrategy,
}
PERIODS_PER_YEAR = {"5m": 288 * 365, "15m": 96 * 365, "1h": 24 * 365, "4h": 6 * 365}


def main(
    family: str,
    symbol: str,
    timeframe: str,
    params_json: str = "{}",
    walk_forward_windows_passed: int = 0,
) -> None:
    settings = load_settings()
    strategy_cls = STRATEGY_REGISTRY[family]
    strategy = strategy_cls(**json.loads(params_json))
    cost_model = CostModel(
        taker_fee_bps=settings.costs.taker_fee_bps,
        slippage_bps=settings.costs.slippage_bps,
        funding_bps_per_8h=settings.costs.funding_bps_per_8h,
    )
    risk_manager = RiskManager(RiskConfig.from_settings(settings.risk))

    result = run_final_evaluation(
        strategy,
        symbol,
        timeframe,
        cost_model,
        risk_manager,
        periods_per_year=PERIODS_PER_YEAR[timeframe],
        walk_forward_windows_passed=walk_forward_windows_passed,
    )

    print(f"HOLDOUT result for {family} on {symbol}/{timeframe}:")
    for line in result.gate_report.summary_lines():
        print(f"  {line}")
    print(f"ALL GATES PASSED: {result.gate_report.all_passed}")
    print(
        "\nThis run is final. If it failed, this strategy is dead — do not tune it and re-run. "
        "Record the outcome in RESULTS.md (if passed) or FINDINGS.md (if failed)."
    )


if __name__ == "__main__":
    typer.run(main)
