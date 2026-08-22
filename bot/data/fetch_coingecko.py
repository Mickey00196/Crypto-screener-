"""CoinGecko public API fetcher — an alternative/supplementary research-data
source to Binance/Bitvavo. Added as ready-to-use scaffolding, NOT wired into
scripts/run_phase1_fetch.py's default flow and not exercised against the
live API this session (see FINDINGS.md: this sandbox's network egress is
blocked to api.coingecko.com the same as every other exchange host — tested
directly during this session). CoinGecko's free tier needs no API key for
the endpoints used here.

Two endpoints, two different shapes, combined into one OHLCV frame:
  - /coins/{id}/ohlc: true OHLC candles, but NO volume, and CoinGecko's free
    tier coarsens granularity for longer lookback windows (daily candles
    beyond ~90 days) — not equivalent to exchange-grade intraday OHLCV.
  - /coins/{id}/market_chart: a volume time series (finer-grained), used
    here to backfill a volume column onto the OHLC candles via nearest-
    timestamp matching.

Returns the same [timestamp, open, high, low, close, volume] shape as
data/fetch_binance.py / data/fetch_bitvavo.py, so it's a drop-in alternative
source for data/validate.py, data/splits.py, and data/storage.py."""

from __future__ import annotations

import pandas as pd
import requests

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# CoinGecko coin ids differ from exchange ticker symbols — extend as needed.
SYMBOL_TO_COINGECKO_ID = {
    "BTC/USDT": "bitcoin",
    "ETH/USDT": "ethereum",
    "BTC/EUR": "bitcoin",
    "ETH/EUR": "ethereum",
}


def fetch_ohlc(
    coingecko_id: str, vs_currency: str, days: int, session: requests.Session | None = None
) -> pd.DataFrame:
    """OHLC candles (no volume) for the trailing `days` days. `days` should
    be one of CoinGecko's accepted values (1,7,14,30,90,180,365,max) for
    predictable granularity — see CoinGecko's API docs."""
    session = session or requests.Session()
    url = f"{COINGECKO_BASE_URL}/coins/{coingecko_id}/ohlc"
    response = session.get(url, params={"vs_currency": vs_currency, "days": days}, timeout=15)
    response.raise_for_status()
    rows = response.json()

    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close"])
    if df.empty:
        df["volume"] = pd.Series(dtype=float)
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df["volume"] = float("nan")  # filled in by fetch_coingecko_ohlcv via the market_chart endpoint
    return df.sort_values("timestamp").drop_duplicates(subset="timestamp").reset_index(drop=True)


def fetch_market_chart_volume(
    coingecko_id: str, vs_currency: str, days: int, session: requests.Session | None = None
) -> pd.DataFrame:
    """The (timestamp, volume) series used to backfill fetch_ohlc's missing
    volume column."""
    session = session or requests.Session()
    url = f"{COINGECKO_BASE_URL}/coins/{coingecko_id}/market_chart"
    response = session.get(url, params={"vs_currency": vs_currency, "days": days}, timeout=15)
    response.raise_for_status()
    payload = response.json()

    df = pd.DataFrame(payload.get("total_volumes", []), columns=["timestamp", "volume"])
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df.sort_values("timestamp").reset_index(drop=True)


def fetch_coingecko_ohlcv(
    symbol: str, vs_currency: str = "usd", days: int = 90, session: requests.Session | None = None
) -> pd.DataFrame:
    if symbol not in SYMBOL_TO_COINGECKO_ID:
        raise ValueError(f"no CoinGecko id mapping for symbol {symbol!r}; add one to SYMBOL_TO_COINGECKO_ID")
    coingecko_id = SYMBOL_TO_COINGECKO_ID[symbol]

    ohlc = fetch_ohlc(coingecko_id, vs_currency, days, session=session)
    if ohlc.empty:
        return ohlc

    volume_series = fetch_market_chart_volume(coingecko_id, vs_currency, days, session=session)
    if volume_series.empty:
        return ohlc

    merged = pd.merge_asof(
        ohlc.sort_values("timestamp"),
        volume_series.sort_values("timestamp"),
        on="timestamp",
        direction="nearest",
        suffixes=("", "_market"),
    )
    merged["volume"] = merged["volume_market"]
    return merged.drop(columns=["volume_market"])[["timestamp", "open", "high", "low", "close", "volume"]]


if __name__ == "__main__":
    import typer

    def main(symbol: str = "BTC/USDT", vs_currency: str = "usd", days: int = 90) -> None:
        df = fetch_coingecko_ohlcv(symbol, vs_currency, days)
        print(f"fetched {len(df)} bars for {symbol} (vs {vs_currency}, {days}d)")

    typer.run(main)
