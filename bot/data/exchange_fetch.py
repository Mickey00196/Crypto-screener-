"""Shared ccxt OHLCV pagination logic used by fetch_binance.py and
fetch_bitvavo.py. Takes an already-constructed ccxt exchange object (dependency
injection) so tests can pass a fake exchange with a canned fetch_ohlcv method
instead of hitting the network — this sandbox has no egress to exchange APIs,
so correctness here is proven via mocked-exchange unit tests, not live calls."""

from __future__ import annotations

from typing import Protocol

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential


class OHLCVExchange(Protocol):
    def fetch_ohlcv(
        self, symbol: str, timeframe: str, since: int | None, limit: int | None
    ) -> list[list[float]]: ...

    def parse_timeframe(self, timeframe: str) -> float: ...


@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
def _fetch_page(
    exchange: OHLCVExchange, symbol: str, timeframe: str, since: int, limit: int
) -> list[list[float]]:
    return exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)


def fetch_ohlcv_history(
    exchange: OHLCVExchange,
    symbol: str,
    timeframe: str,
    since_ms: int,
    until_ms: int | None = None,
    limit: int = 1000,
    max_pages: int = 100_000,
) -> pd.DataFrame:
    """Paginate through exchange.fetch_ohlcv from since_ms up to (but not
    including) until_ms, or through to "now" if until_ms is None. Dedupes,
    sorts, and returns a DataFrame with columns
    [timestamp(UTC datetime), open, high, low, close, volume]."""
    all_rows: list[list[float]] = []
    cursor = since_ms
    tf_ms = int(exchange.parse_timeframe(timeframe) * 1000)
    pages = 0

    while pages < max_pages:
        rows = _fetch_page(exchange, symbol, timeframe, cursor, limit)
        pages += 1
        if not rows:
            break
        all_rows.extend(rows)
        last_ts = rows[-1][0]
        next_cursor = last_ts + tf_ms
        if next_cursor <= cursor:
            # pagination isn't advancing — stop rather than looping forever
            break
        cursor = next_cursor
        if until_ms is not None and cursor >= until_ms:
            break
        if until_ms is None and len(rows) < limit:
            # Open-ended fetch (no until_ms): a short page is a reasonable
            # signal we've reached "now". When until_ms IS set, a short page
            # partway through the requested range does NOT mean we're done —
            # some exchanges (confirmed: Bitvavo) return fewer than `limit`
            # rows for a given `since` even with much more history still
            # ahead before `until_ms`. Stopping here silently truncated a
            # requested 90-day fetch to ~42 days in production. Only stop
            # early when there's no explicit end to reach.
            break

    df = pd.DataFrame(all_rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    if until_ms is not None:
        until_dt = pd.to_datetime(until_ms, unit="ms", utc=True)
        df = df[df["timestamp"] < until_dt]
    return df.drop_duplicates(subset="timestamp").sort_values("timestamp").reset_index(drop=True)
