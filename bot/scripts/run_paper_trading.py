"""Start (or resume) the paper-trading loop. Defaults to TRADING_MODE=paper
regardless of what's in the environment unless explicitly overridden — the
hard rule's belt-and-suspenders default.

NOT RUN continuously in this session: it needs live Bitvavo market data,
which this sandbox cannot reach (see bot/FINDINGS.md). live/trading_loop.py
is fully unit-tested with a mocked data source; run this for real once
network access exists, and let it accumulate the >=2 weeks of paper-trading
history Phase 5 requires.

Run: python scripts/run_paper_trading.py --family trend_filtered_pullback --symbol BTC/EUR --timeframe 1h
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import typer

from engine.costs import CostModel
from live.trading_loop import TradingLoop
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
BOT_ROOT = Path(__file__).resolve().parent.parent


def main(
    family: str = "trend_filtered_pullback",
    symbol: str = "BTC/EUR",
    timeframe: str = "1h",
    params_json: str = "{}",
    state_path: str = str(BOT_ROOT / "live" / "paper_state.json"),
) -> None:
    trading_mode = os.environ.get("TRADING_MODE", "paper")
    if trading_mode == "live":
        typer.confirm(
            "TRADING_MODE=live is set — this will place REAL orders with REAL money. Continue?", abort=True
        )

    settings = load_settings()
    strategy_cls = STRATEGY_REGISTRY[family]
    strategy = strategy_cls(**json.loads(params_json))
    cost_model = CostModel(
        taker_fee_bps=settings.costs.taker_fee_bps,
        slippage_bps=settings.costs.slippage_bps,
        funding_bps_per_8h=settings.costs.funding_bps_per_8h,
    )
    risk_manager = RiskManager(RiskConfig.from_settings(settings.risk))

    loop = TradingLoop(
        strategy=strategy,
        risk_manager=risk_manager,
        symbol=symbol,
        timeframe=timeframe,
        cost_model=cost_model,
        state_path=state_path,
        trading_mode=trading_mode,
    )
    print(f"Starting {trading_mode} trading loop: {family} on {symbol}/{timeframe}. State at {state_path}")
    asyncio.run(loop.run_forever())


if __name__ == "__main__":
    typer.run(main)
