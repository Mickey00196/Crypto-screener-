"""[SYNTHETIC SMOKE TEST] — exercises the full data -> engine -> optimizer ->
walk-forward -> gates pipeline end to end on SYNTHETIC data (data/synthetic.py).

This is NOT a strategy-quality result. It proves the machinery runs
correctly end to end; it says nothing about whether any strategy has real
edge. Every row it logs to EXPERIMENTS.md is tagged "[SYNTHETIC SMOKE TEST]"
so it can never be confused with a real finding. Real data fetch (Phase 1)
is blocked in this sandbox by network policy — see bot/FINDINGS.md — so this
is the closest thing to an end-to-end proof available this session.

Run: python scripts/run_pipeline_smoketest.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from data.synthetic import generate_synthetic_ohlcv
from engine.costs import CostModel
from evaluation.aggregate import evaluate_strategy
from evaluation.gates import check_gates
from evaluation.walk_forward import generate_walk_forward_windows
from optimization.runner import run_family_optimization
from risk.risk_manager import RiskConfig, RiskManager
from strategies.trend_continuation_confluence import TrendContinuationConfluenceStrategy
from strategies.trend_filtered_pullback import TrendFilteredPullbackStrategy
from strategies.volatility_breakout_trend import VolatilityBreakoutTrendStrategy

BOT_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS_LOG = BOT_ROOT / "EXPERIMENTS.md"
TAG = "[SYNTHETIC SMOKE TEST]"
PERIODS_PER_YEAR = 24 * 365  # hourly bars

FAMILIES = {
    "TrendFilteredPullbackStrategy": (
        TrendFilteredPullbackStrategy,
        {
            "ema_period": [50, 100, 150],
            "adx_period": [10, 14, 20],
            "adx_threshold": [15.0, 20.0, 25.0],
            "rsi_period": [10, 14],
            "rsi_entry": [30.0, 35.0, 40.0],
            "rsi_exit": [50.0, 55.0, 60.0],
        },
    ),
    "VolatilityBreakoutTrendStrategy": (
        VolatilityBreakoutTrendStrategy,
        {
            "donchian_period": [10, 20, 30],
            "st_period": [7, 10, 14],
            "st_multiplier": [2.0, 3.0, 4.0],
            "obv_lookback": [3, 5, 8],
        },
    ),
    "TrendContinuationConfluenceStrategy": (
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


def _risk_manager_factory() -> RiskManager:
    return RiskManager(
        RiskConfig(
            max_risk_per_trade_pct=1.0,
            max_position_pct=20.0,
            max_concurrent_positions=3,
            daily_loss_limit_pct=3.0,
            max_drawdown_kill_switch_pct=15.0,
            atr_period=14,
        )
    )


def main() -> None:
    cost_model = CostModel(taker_fee_bps=25.0, slippage_bps=5.0)

    # 2 synthetic "symbols" standing in for BTC/USDT and ETH/USDT this pass.
    full_series = {
        "SYNTH/A": generate_synthetic_ohlcv(n_bars=4000, timeframe="1h", regime="mixed", seed=101),
        "SYNTH/B": generate_synthetic_ohlcv(n_bars=4000, timeframe="1h", regime="mixed", seed=202),
    }
    train_datasets = {
        k: df.iloc[: int(len(df) * 0.6)].reset_index(drop=True) for k, df in full_series.items()
    }
    val_datasets = {
        k: df.iloc[int(len(df) * 0.6) : int(len(df) * 0.8)].reset_index(drop=True)
        for k, df in full_series.items()
    }
    train_val_datasets = {
        k: df.iloc[: int(len(df) * 0.8)].reset_index(drop=True) for k, df in full_series.items()
    }

    dataset_summary = ", ".join(
        f"{k}({len(v)} train, {len(val_datasets[k])} val)" for k, v in train_datasets.items()
    )
    print(f"{TAG} Datasets: {dataset_summary}")

    all_family_results = {}
    for name, (cls, param_space) in FAMILIES.items():
        print(f"\n{TAG} Running optimization sweep for {name} (budget: 12 configs)...")
        results = run_family_optimization(
            cls,
            param_space,
            n_configs=12,
            seed=42,
            train_datasets=train_datasets,
            val_datasets=val_datasets,
            cost_model=cost_model,
            risk_manager_factory=_risk_manager_factory,
            periods_per_year=PERIODS_PER_YEAR,
            experiments_log_path=EXPERIMENTS_LOG,
            tag=TAG,
        )
        all_family_results[name] = results
        n_candidates = sum(1 for r in results if r.verdict == "CANDIDATE")
        print(f"{TAG} {name}: {len(results)} configs run, {n_candidates} not overfit-rejected")

        # pick the best (by val expectancy) surviving candidate and run walk-forward on it
        candidates = [r for r in results if r.verdict == "CANDIDATE"]
        if not candidates:
            print(f"{TAG} {name}: no candidate survived the overfit check on this synthetic slice")
            continue
        best = max(candidates, key=lambda r: r.val_metrics.expectancy)
        strategy = cls(**best.params)

        one_series = train_val_datasets["SYNTH/A"]
        windows = generate_walk_forward_windows(
            one_series,
            train_period=pd.Timedelta(days=45),
            test_period=pd.Timedelta(days=10),
            step=pd.Timedelta(days=10),
            embargo=pd.Timedelta(hours=6),
        )
        passed = 0
        for w in windows:
            agg = evaluate_strategy(
                strategy, {"SYNTH/A": w.test}, cost_model, _risk_manager_factory, PERIODS_PER_YEAR
            )
            if agg.pooled_metrics.expectancy > 0:
                passed += 1
        print(
            f"{TAG} {name}: walk-forward on best candidate — "
            f"{passed}/{len(windows)} windows positive expectancy"
        )

        gate_report = check_gates(
            best.val_metrics, walk_forward_windows_passed=passed, min_walk_forward_windows=3
        )
        print(f"{TAG} {name}: Definition-of-Done gates on validation — all_passed={gate_report.all_passed}")
        for line in gate_report.summary_lines():
            print(f"{TAG}   {line}")

    print(f"\n{TAG} Done. Rows appended to {EXPERIMENTS_LOG.relative_to(BOT_ROOT)}.")
    print(
        f"{TAG} Reminder: these are SYNTHETIC results proving the pipeline runs end to end, "
        "not a claim about real strategy edge. See FINDINGS.md."
    )


if __name__ == "__main__":
    main()
