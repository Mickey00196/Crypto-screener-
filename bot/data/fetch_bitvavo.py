"""Bitvavo public OHLCV fetch (EUR-quoted pairs — used for paper-trading live
bars and for documenting the Binance-USDT-vs-Bitvavo-EUR basis). NOT executed
against the live network in this session: this sandbox's proxy returns 403
policy-denial for api.bitvavo.com (confirmed via curl and the proxy status
log — see bot/FINDINGS.md). Bitvavo also has no public testnet/sandbox, so
paper trading here means simulating fills locally against real public bars
once fetched (see live/paper_broker.py), never routing through a sandbox
exchange. The fetch logic itself is real and unit-tested against a mocked
exchange in tests/test_data/test_fetch.py."""

from __future__ import annotations

from datetime import UTC, datetime

import ccxt
import pandas as pd

from data.exchange_fetch import fetch_ohlcv_history


def make_bitvavo_exchange(api_key: str | None = None, api_secret: str | None = None) -> ccxt.bitvavo:
    """Public OHLCV needs no credentials. Credentials are accepted here only
    for the live-order path (live/live_broker.py), never for paper mode."""
    config: dict = {"enableRateLimit": True}
    if api_key and api_secret:
        config["apiKey"] = api_key
        config["secret"] = api_secret
    return ccxt.bitvavo(config)


def fetch_bitvavo_ohlcv(
    symbol: str,
    timeframe: str,
    since: datetime,
    until: datetime | None = None,
    exchange: ccxt.bitvavo | None = None,
) -> pd.DataFrame:
    exchange = exchange or make_bitvavo_exchange()
    since_ms = int(since.timestamp() * 1000)
    until_ms = int(until.timestamp() * 1000) if until else None
    return fetch_ohlcv_history(exchange, symbol, timeframe, since_ms, until_ms)


if __name__ == "__main__":
    import typer

    def main(symbol: str = "BTC/EUR", timeframe: str = "1h", days: int = 30) -> None:
        from datetime import timedelta

        since = datetime.now(UTC) - timedelta(days=days)
        df = fetch_bitvavo_ohlcv(symbol, timeframe, since)
        print(f"fetched {len(df)} bars for {symbol}/{timeframe}")

    typer.run(main)
