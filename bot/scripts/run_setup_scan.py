"""Daily setup scan — the Railway cron entrypoint.

Fetches daily candles (Coinbase/Bitvavo public data, no API keys), stores
them in Postgres, builds weekly candles, and prints the setup for each
symbol: state, base, channel, zone, trigger, targets, invalidation.

Environment (all optional):
  SCAN_SYMBOLS        comma-separated exchange:SYMBOL list
                      (default coinbase:AERO/USD,coinbase:BTC/USD,coinbase:ETH/USD)
  DATABASE_URL        Postgres URL; without it every run re-fetches the full
                      lookback and no scenario log is kept
  TELEGRAM_BOT_TOKEN  with TELEGRAM_CHAT_ID: also send the summary to Telegram
  TELEGRAM_CHAT_ID

Run: python scripts/run_setup_scan.py [--symbols coinbase:SOL/USD] [--json]
"""

from __future__ import annotations

import json
import os

import typer

from data.candle_db import get_engine
from setups.notify import send_telegram, telegram_config
from setups.scan import DEFAULT_LOOKBACK_DAYS, DEFAULT_SYMBOLS, parse_symbols, run_scan
from setups.scenario import describe


def main(
    symbols: str = typer.Option(os.environ.get("SCAN_SYMBOLS", DEFAULT_SYMBOLS), help="exchange:SYMBOL,..."),
    lookback_days: int = typer.Option(DEFAULT_LOOKBACK_DAYS, help="days of daily candles to analyze"),
    as_json: bool = typer.Option(False, "--json", help="also print each setup as JSON"),
) -> None:
    engine = get_engine() if os.environ.get("DATABASE_URL") else None
    if engine is None:
        print("DATABASE_URL not set: fetching the full lookback, no scenario log kept.\n")

    results = run_scan(parse_symbols(symbols), engine=engine, lookback_days=lookback_days)

    blocks, failures = [], 0
    for exchange, symbol, result in results:
        if isinstance(result, Exception):
            failures += 1
            blocks.append(f"{exchange}:{symbol} FAILED: {result!r}")
            continue
        blocks.append(describe(result))
        if as_json:
            print(json.dumps(result.to_dict(), default=str))
    summary = "\n\n".join(blocks)
    print(summary, flush=True)

    telegram = telegram_config()
    if telegram:
        try:
            send_telegram(summary, *telegram)
        except Exception as exc:  # noqa: BLE001 — the scan itself succeeded; don't fail the run
            print(f"Telegram send failed: {exc!r}")

    if results and failures == len(results):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    typer.run(main)
