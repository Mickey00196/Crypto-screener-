"""Binance public OHLCV fetch (research/backtest history — deepest free
history, no API key required). NOT executed against the live network in this
session: this sandbox's proxy returns 403 policy-denial for api.binance.com
(confirmed via curl and the proxy status log — see bot/FINDINGS.md). The
fetch logic itself is real and unit-tested against a mocked exchange in
tests/test_data/test_fetch.py; run this for real once network egress exists."""

from __future__ import annotations

from datetime import UTC, datetime

import ccxt
import pandas as pd

from data.exchange_fetch import fetch_ohlcv_history


def make_binance_exchange() -> ccxt.binance:
    return ccxt.binance({"enableRateLimit": True})


def fetch_binance_ohlcv(
    symbol: str,
    timeframe: str,
    since: datetime,
    until: datetime | None = None,
    exchange: ccxt.binance | None = None,
) -> pd.DataFrame:
    exchange = exchange or make_binance_exchange()
    since_ms = int(since.timestamp() * 1000)
    until_ms = int(until.timestamp() * 1000) if until else None
    return fetch_ohlcv_history(exchange, symbol, timeframe, since_ms, until_ms)


if __name__ == "__main__":
    import typer

    def main(symbol: str = "BTC/USDT", timeframe: str = "1h", years: int = 3) -> None:
        since = datetime.now(UTC).replace(year=datetime.now(UTC).year - years)
        df = fetch_binance_ohlcv(symbol, timeframe, since)
        print(f"fetched {len(df)} bars for {symbol}/{timeframe}")

    typer.run(main)
