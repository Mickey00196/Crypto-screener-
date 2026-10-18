"""Coinbase public OHLCV fetch (USD-quoted pairs such as AERO/USD, BTC/USD).

Public candles need no API key. Coinbase reachability matters for where this
runs: Railway's us-west2 region reaches US exchanges, but Binance answers
HTTP 451 there (see FINDINGS.md), so Coinbase is the default source for the
setup scanner.

Coinbase's candles endpoint is windowed: each request returns at most 300
candles between a start and an end time, and windows before a coin was
listed come back EMPTY. The shared fetch_ohlcv_history helper stops at the
first empty page, which would return nothing for a lookback that starts
before listing (AERO, for example). So this fetcher walks fixed windows from
`since` to `until` and simply skips empty ones."""

from __future__ import annotations

from datetime import UTC, datetime

import ccxt
import pandas as pd

from data.exchange_fetch import OHLCVExchange, _fetch_page

COINBASE_MAX_CANDLES = 300
COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def make_coinbase_exchange() -> ccxt.coinbaseexchange:
    """ccxt's `coinbaseexchange` uses Coinbase's public market-data API —
    no credentials, no account needed."""
    return ccxt.coinbaseexchange({"enableRateLimit": True})


def fetch_windowed_history(
    exchange: OHLCVExchange,
    symbol: str,
    timeframe: str,
    since_ms: int,
    until_ms: int,
    limit: int = COINBASE_MAX_CANDLES,
) -> pd.DataFrame:
    """Fetch [since_ms, until_ms) as consecutive windows of `limit` candles,
    skipping windows that return no rows (e.g. before the pair was listed)."""
    if until_ms <= since_ms:
        return pd.DataFrame(columns=COLUMNS)

    tf_ms = int(exchange.parse_timeframe(timeframe) * 1000)
    window_ms = limit * tf_ms
    rows: list[list[float]] = []
    # Align to a candle boundary: ccxt then asks Coinbase for exactly `limit`
    # candles per window, and the first (partial-day) candle isn't dropped.
    cursor = since_ms - (since_ms % tf_ms)
    while cursor < until_ms:
        window_end = min(cursor + window_ms, until_ms)
        page = _fetch_page(exchange, symbol, timeframe, cursor, limit)
        rows.extend(r for r in page if cursor <= r[0] < window_end)
        cursor = window_end

    df = pd.DataFrame(rows, columns=COLUMNS)
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df.drop_duplicates(subset="timestamp").sort_values("timestamp").reset_index(drop=True)


def fetch_coinbase_ohlcv(
    symbol: str,
    timeframe: str,
    since: datetime,
    until: datetime | None = None,
    exchange: OHLCVExchange | None = None,
) -> pd.DataFrame:
    exchange = exchange or make_coinbase_exchange()
    until = until or datetime.now(UTC)
    return fetch_windowed_history(
        exchange, symbol, timeframe, int(since.timestamp() * 1000), int(until.timestamp() * 1000)
    )


if __name__ == "__main__":
    import typer

    def main(symbol: str = "AERO/USD", timeframe: str = "1d", days: int = 365) -> None:
        from datetime import timedelta

        since = datetime.now(UTC) - timedelta(days=days)
        df = fetch_coinbase_ohlcv(symbol, timeframe, since)
        print(f"fetched {len(df)} bars for {symbol}/{timeframe}")

    typer.run(main)
