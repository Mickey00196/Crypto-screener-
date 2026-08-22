"""Replays historical bars through the REAL live/trading_loop.py code path
(TradingLoop.process_latest_closed_bar — the same method scripts/
run_paper_trading.py calls every bar in production) to populate
live/paper_state.json with real, non-fabricated output from the actual
strategy -> risk-manager -> paper-broker pipeline.

This is a DEMONSTRATION/verification tool, not a backtest: it does not use
engine/backtester.py's vectorized-ish loop at all — it drives the exact
same TradingLoop class the live paper-trading process uses, one bar at a
time, so what you see in the dashboard afterward is proof the live
plumbing works end to end, not just that the backtester does.

Data: SYNTHETIC (data/synthetic.py) — this sandbox's network egress cannot
reach any exchange (see FINDINGS.md), so no real market data is available
this session. Every symbol name and printed line is prefixed SYNTH/ or
tagged accordingly so this is never confused with real trading activity.

Run: python scripts/replay_demo.py --strategy trend_filtered_pullback --bars 3000
"""

from __future__ import annotations

from pathlib import Path

import typer

from data.synthetic import generate_synthetic_ohlcv
from engine.costs import CostModel
from live.trading_loop import TradingLoop
from risk.risk_manager import RiskConfig, RiskManager
from strategies.trend_continuation_confluence import TrendContinuationConfluenceStrategy
from strategies.trend_filtered_pullback import TrendFilteredPullbackStrategy
from strategies.volatility_breakout_trend import VolatilityBreakoutTrendStrategy

BOT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_PATH = BOT_ROOT / "live" / "paper_state.json"

STRATEGY_REGISTRY = {
    "trend_filtered_pullback": TrendFilteredPullbackStrategy,
    "volatility_breakout_trend": VolatilityBreakoutTrendStrategy,
    "trend_continuation_confluence": TrendContinuationConfluenceStrategy,
}


def main(
    strategy: str = "trend_filtered_pullback",
    symbol: str = "SYNTH/DEMO",
    timeframe: str = "1h",
    bars: int = 3000,
    seed: int = 7,
    warmup: int = 210,
    state_path: str = str(DEFAULT_STATE_PATH),
) -> None:
    if state_path == str(DEFAULT_STATE_PATH) and Path(state_path).exists():
        Path(state_path).unlink()  # start this demo from a clean slate

    strategy_cls = STRATEGY_REGISTRY[strategy]
    df = generate_synthetic_ohlcv(n_bars=bars, timeframe=timeframe, regime="mixed", seed=seed)

    loop = TradingLoop(
        strategy=strategy_cls(),
        risk_manager=RiskManager(
            RiskConfig(
                max_risk_per_trade_pct=1.0,
                max_position_pct=20.0,
                max_concurrent_positions=3,
                daily_loss_limit_pct=3.0,
                max_drawdown_kill_switch_pct=15.0,
                atr_period=14,
            )
        ),
        symbol=symbol,
        timeframe=timeframe,
        cost_model=CostModel(taker_fee_bps=25.0, slippage_bps=5.0),
        state_path=state_path,
        trading_mode="paper",
    )

    # Feed the loop one "latest closed bar" window at a time, exactly as the
    # live process would see an ever-growing window of real bars.
    for i in range(warmup, len(df)):
        window = df.iloc[: i + 1].reset_index(drop=True)
        loop.process_latest_closed_bar(window)

    n_trades = len(loop.state.trade_log)
    n_open = len(loop.state.positions)
    print(f"[SYNTHETIC DEMO] {strategy} on {symbol}/{timeframe}: {bars} bars replayed through the live loop")
    print(
        f"[SYNTHETIC DEMO] closed trades: {n_trades}, open positions: {n_open}, "
        f"cash: {loop.state.cash:.2f}"
    )
    if n_trades:
        pnls = [t["pnl"] for t in loop.state.trade_log]
        wins = sum(1 for p in pnls if p > 0)
        print(
            f"[SYNTHETIC DEMO] win rate: {wins}/{n_trades} = {wins / n_trades:.1%}, "
            f"total pnl: {sum(pnls):.2f}"
        )
    print(f"[SYNTHETIC DEMO] state written to {state_path}")


if __name__ == "__main__":
    typer.run(main)
