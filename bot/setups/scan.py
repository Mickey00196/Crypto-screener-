"""Daily scan: fetch daily candles, store them, build weekly candles,
analyze, and log the scenario.

Runs on Railway (which can reach Coinbase and Bitvavo) as a cron job via
scripts/run_setup_scan.py. With a database, each run only re-fetches the
last few days and upserts them; without one it fetches the full lookback
every time and logs nothing."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pandas as pd
from sqlalchemy import Engine
from tenacity import RetryError

from data.candle_db import latest_timestamp, load_candles, save_scenario, upsert_candles
from data.resample import resample_ohlcv
from setups.scenario import Setup, analyze

Fetcher = Callable[[str, str, datetime, datetime], pd.DataFrame]

DEFAULT_SYMBOLS = "coinbase:AERO/USD,coinbase:BTC/USD,coinbase:ETH/USD"
FETCH_TIMEFRAME = "1d"
DEFAULT_LOOKBACK_DAYS = 1100  # ~3 years of daily candles = ~157 weekly candles
REFETCH_OVERLAP = timedelta(days=3)  # re-pull recent days: the last one was still forming


def default_fetchers() -> dict[str, Fetcher]:
    from data.fetch_bitvavo import fetch_bitvavo_ohlcv
    from data.fetch_coinbase import fetch_coinbase_ohlcv

    return {"coinbase": fetch_coinbase_ohlcv, "bitvavo": fetch_bitvavo_ohlcv}


def parse_symbols(spec: str) -> list[tuple[str, str]]:
    """'coinbase:AERO/USD, bitvavo:BTC/EUR' -> [('coinbase', 'AERO/USD'), ('bitvavo', 'BTC/EUR')]"""
    pairs = []
    for item in filter(None, (s.strip() for s in spec.split(","))):
        exchange, sep, symbol = item.partition(":")
        if not sep or not symbol:
            raise ValueError(f"expected exchange:SYMBOL, got {item!r}")
        pairs.append((exchange.strip().lower(), symbol.strip().upper()))
    return pairs


def update_candles(
    engine: Engine | None,
    exchange: str,
    symbol: str,
    fetch: Fetcher,
    now: datetime,
    lookback_days: int,
) -> pd.DataFrame:
    window_start = now - timedelta(days=lookback_days)
    if engine is None:
        return fetch(symbol, FETCH_TIMEFRAME, window_start, now)

    latest = latest_timestamp(engine, exchange, symbol, FETCH_TIMEFRAME)
    since = window_start if latest is None else max(window_start, latest.to_pydatetime() - REFETCH_OVERLAP)
    upsert_candles(engine, exchange, symbol, FETCH_TIMEFRAME, fetch(symbol, FETCH_TIMEFRAME, since, now))
    return load_candles(engine, exchange, symbol, FETCH_TIMEFRAME, since=window_start)


def scan_symbol(
    engine: Engine | None,
    exchange: str,
    symbol: str,
    fetch: Fetcher,
    now: datetime,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    timeframe: str = "1w",
) -> Setup:
    daily = update_candles(engine, exchange, symbol, fetch, now, lookback_days)
    if daily.empty:
        raise ValueError(f"no candles returned for {exchange}:{symbol}")
    setup = analyze(resample_ohlcv(daily, timeframe), symbol=symbol, timeframe=timeframe)
    if engine is not None:
        save_scenario(engine, exchange, symbol, timeframe, setup.to_dict(), run_at=now)
    return setup


def run_scan(
    symbols: list[tuple[str, str]],
    engine: Engine | None = None,
    fetchers: dict[str, Fetcher] | None = None,
    now: datetime | None = None,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> list[tuple[str, str, Setup | Exception]]:
    """Scan every symbol; one symbol failing (delisted, rate-limited, ...)
    doesn't stop the others. Returns (exchange, symbol, Setup or error)."""
    fetchers = fetchers or default_fetchers()
    now = now or datetime.now(UTC)
    results: list[tuple[str, str, Setup | Exception]] = []
    for exchange, symbol in symbols:
        try:
            if exchange not in fetchers:
                raise ValueError(f"unknown exchange {exchange!r}; available: {sorted(fetchers)}")
            setup = scan_symbol(engine, exchange, symbol, fetchers[exchange], now, lookback_days)
            results.append((exchange, symbol, setup))
        except Exception as exc:  # noqa: BLE001 — report and move on to the next symbol
            if isinstance(exc, RetryError) and exc.last_attempt.exception() is not None:
                exc = exc.last_attempt.exception()  # show the exchange error, not the retry wrapper
            results.append((exchange, symbol, exc))
    return results
