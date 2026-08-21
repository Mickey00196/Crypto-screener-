"""Crypto-specific indicators: funding rate, open interest change, long/short
ratio, basis, exchange netflow.

UNAVAILABLE THIS PASS. data/fetch_binance.py and data/fetch_bitvavo.py only
fetch SPOT OHLCV (public candle endpoints) — none of these signals exist in
spot market data. Funding rate / open interest / long-short ratio require a
perpetual-futures data feed; basis requires both spot and futures prices;
exchange netflow requires an on-chain data provider. See RESEARCH.md §2.4
for why funding/basis carry was evaluated but not selected as one of the 3
implemented strategy families this pass (also blocked on this same gap).

Every function below raises NotImplementedError with a message naming the
missing data source, rather than silently returning zeros/NaNs — a strategy
that accidentally called one of these should fail loudly, not degrade into
an always-false filter."""

from __future__ import annotations

import pandas as pd


def funding_rate(df: pd.DataFrame) -> pd.Series:
    raise NotImplementedError(
        "funding rate requires a perpetual-futures data feed (e.g. Binance/Bitvavo "
        "futures funding endpoints); this pass only fetches spot OHLCV."
    )


def open_interest_change(df: pd.DataFrame) -> pd.Series:
    raise NotImplementedError(
        "open interest requires a perpetual-futures data feed; this pass only fetches spot OHLCV."
    )


def long_short_ratio(df: pd.DataFrame) -> pd.Series:
    raise NotImplementedError(
        "long/short ratio requires an exchange futures-positioning endpoint not fetched this pass."
    )


def basis(spot_df: pd.DataFrame, futures_df: pd.DataFrame) -> pd.Series:
    raise NotImplementedError(
        "basis requires both spot and perpetual-futures price series; this pass only fetches spot OHLCV."
    )


def exchange_netflow(df: pd.DataFrame) -> pd.Series:
    raise NotImplementedError(
        "exchange netflow requires an on-chain data provider (e.g. Glassnode/CryptoQuant-style "
        "API), not integrated this pass."
    )
