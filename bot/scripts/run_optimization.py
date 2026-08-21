"""Run the real 50-config-per-family optimization sweep (Phase 4) against
real fetched data (scripts/run_phase1_fetch.py must have been run first —
this reads train/val splits via data/storage.py, never holdout). Mirrors
scripts/run_pipeline_smoketest.py's structure but against real data and the
full budget instead of a 12-config synthetic dry run.

Run: python scripts/run_optimization.py --family trend_filtered_pullback
"""

from __future__ import annotations

from pathlib import Path

import typer

from data.storage import load_split
from engine.costs import CostModel
from optimization.runner import run_family_optimization
from risk.risk_manager import RiskConfig, RiskManager
from settings import load_settings
from strategies.trend_continuation_confluence import TrendContinuationConfluenceStrategy
from strategies.trend_filtered_pullback import TrendFilteredPullbackStrategy
from strategies.volatility_breakout_trend import VolatilityBreakoutTrendStrategy

BOT_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS_LOG = BOT_ROOT / "EXPERIMENTS.md"
PERIODS_PER_YEAR = {"5m": 288 * 365, "15m": 96 * 365, "1h": 24 * 365, "4h": 6 * 365}

FAMILIES = {
    "trend_filtered_pullback": (
        TrendFilteredPullbackStrategy,
        {
            "ema_period": [50, 100, 150, 200],
            "adx_period": [10, 14, 20],
            "adx_threshold": [15.0, 20.0, 25.0],
            "rsi_period": [10, 14],
            "rsi_entry": [30.0, 35.0, 40.0],
            "rsi_exit": [50.0, 55.0, 60.0],
        },
    ),
    "volatility_breakout_trend": (
        VolatilityBreakoutTrendStrategy,
        {
            "donchian_period": [10, 20, 30, 55],
            "st_period": [7, 10, 14],
            "st_multiplier": [2.0, 3.0, 4.0],
            "obv_lookback": [3, 5, 8],
        },
    ),
    "trend_continuation_confluence": (
        TrendContinuationConfluenceStrategy,
        {
            "ema_fast": [10, 20, 30],
            "ema_slow": [40, 50, 60],
            "macd_fast": [8, 12],
            "macd_slow": [21, 26],
            "rsi_period": [10, 14],
            "rsi_pullback_long": [45.0, 50.0, 55.0],
        },
    ),
}


def _risk_manager_factory(risk_settings) -> RiskManager:
    return RiskManager(RiskConfig.from_settings(risk_settings))


def main(
    family: str = "trend_filtered_pullback", timeframe: str = "1h", n_configs: int = 50, seed: int = 42
) -> None:
    """One timeframe per run — datasets of different timeframes have
    different periods_per_year, so mixing them in a single Sortino
    calculation would be invalid. Run once per timeframe in settings.yaml."""
    settings = load_settings()
    if timeframe not in settings.timeframes:
        raise typer.BadParameter(f"timeframe must be one of {settings.timeframes}")
    cls, param_space = FAMILIES[family]
    cost_model = CostModel(
        taker_fee_bps=settings.costs.taker_fee_bps,
        slippage_bps=settings.costs.slippage_bps,
        funding_bps_per_8h=settings.costs.funding_bps_per_8h,
    )

    train_datasets = {symbol: load_split(symbol, timeframe, "train") for symbol in settings.pairs}
    val_datasets = {symbol: load_split(symbol, timeframe, "val") for symbol in settings.pairs}
    periods_per_year = PERIODS_PER_YEAR[timeframe]

    results = run_family_optimization(
        cls,
        param_space,
        n_configs=n_configs,
        seed=seed,
        train_datasets=train_datasets,
        val_datasets=val_datasets,
        cost_model=cost_model,
        risk_manager_factory=lambda: _risk_manager_factory(settings.risk),
        periods_per_year=periods_per_year,
        experiments_log_path=EXPERIMENTS_LOG,
        tag=f"[REAL:{family}:{timeframe}]",
    )
    n_candidates = sum(1 for r in results if r.verdict == "CANDIDATE")
    print(f"{family}: {len(results)} configs run, {n_candidates} candidates survived the overfit check")
    print(f"Logged to {EXPERIMENTS_LOG}")


if __name__ == "__main__":
    typer.run(main)
