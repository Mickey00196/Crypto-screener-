"""Unit tests for the CoinGecko fetcher against a MOCKED HTTP API (via the
`responses` library) — this sandbox's network egress is blocked to
api.coingecko.com (confirmed directly this session, same as every other
exchange host; see bot/FINDINGS.md), so correctness is proven here via
mocked HTTP responses shaped exactly like CoinGecko's real API, not a live
call."""

import pandas as pd
import pytest
import requests
import responses

from data.fetch_coingecko import (
    COINGECKO_BASE_URL,
    fetch_coingecko_ohlcv,
    fetch_market_chart_volume,
    fetch_ohlc,
)


@responses.activate
def test_fetch_ohlc_parses_rows_into_expected_shape():
    responses.add(
        responses.GET,
        f"{COINGECKO_BASE_URL}/coins/bitcoin/ohlc",
        json=[
            [1700000000000, 100.0, 110.0, 90.0, 105.0],
            [1700003600000, 105.0, 115.0, 95.0, 108.0],
        ],
        status=200,
    )
    df = fetch_ohlc("bitcoin", "usd", days=1)
    assert len(df) == 2
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert df["open"].iloc[0] == 100.0
    assert df["timestamp"].iloc[0] == pd.Timestamp(1700000000000, unit="ms", tz="UTC")


@responses.activate
def test_fetch_ohlc_empty_response_returns_empty_dataframe_with_columns():
    responses.add(responses.GET, f"{COINGECKO_BASE_URL}/coins/bitcoin/ohlc", json=[], status=200)
    df = fetch_ohlc("bitcoin", "usd", days=1)
    assert df.empty
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]


@responses.activate
def test_fetch_ohlc_raises_on_http_error():
    responses.add(responses.GET, f"{COINGECKO_BASE_URL}/coins/bitcoin/ohlc", status=429)
    with pytest.raises(requests.HTTPError):
        fetch_ohlc("bitcoin", "usd", days=1)


@responses.activate
def test_fetch_market_chart_volume_parses_rows():
    responses.add(
        responses.GET,
        f"{COINGECKO_BASE_URL}/coins/bitcoin/market_chart",
        json={
            "prices": [],
            "market_caps": [],
            "total_volumes": [[1700000000000, 12345.0], [1700003600000, 6789.0]],
        },
        status=200,
    )
    df = fetch_market_chart_volume("bitcoin", "usd", days=1)
    assert len(df) == 2
    assert df["volume"].iloc[0] == 12345.0


@responses.activate
def test_fetch_coingecko_ohlcv_merges_volume_by_nearest_timestamp():
    responses.add(
        responses.GET,
        f"{COINGECKO_BASE_URL}/coins/bitcoin/ohlc",
        json=[[1700000000000, 100.0, 110.0, 90.0, 105.0]],
        status=200,
    )
    responses.add(
        responses.GET,
        f"{COINGECKO_BASE_URL}/coins/bitcoin/market_chart",
        json={"total_volumes": [[1700000000000, 999.0]]},
        status=200,
    )
    df = fetch_coingecko_ohlcv("BTC/USDT", vs_currency="usd", days=1)
    assert len(df) == 1
    assert df["volume"].iloc[0] == 999.0
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]


@responses.activate
def test_fetch_coingecko_ohlcv_falls_back_to_ohlc_only_when_volume_empty():
    responses.add(
        responses.GET,
        f"{COINGECKO_BASE_URL}/coins/bitcoin/ohlc",
        json=[[1700000000000, 100.0, 110.0, 90.0, 105.0]],
        status=200,
    )
    responses.add(
        responses.GET,
        f"{COINGECKO_BASE_URL}/coins/bitcoin/market_chart",
        json={"total_volumes": []},
        status=200,
    )
    df = fetch_coingecko_ohlcv("BTC/USDT")
    assert len(df) == 1
    assert pd.isna(df["volume"].iloc[0])


def test_fetch_coingecko_ohlcv_rejects_unmapped_symbol():
    with pytest.raises(ValueError, match="no CoinGecko id mapping"):
        fetch_coingecko_ohlcv("DOGE/USDT")


@responses.activate
def test_fetch_coingecko_ohlcv_empty_ohlc_short_circuits_without_volume_call():
    responses.add(responses.GET, f"{COINGECKO_BASE_URL}/coins/bitcoin/ohlc", json=[], status=200)
    df = fetch_coingecko_ohlcv("BTC/USDT")
    assert df.empty
    # only one HTTP call should have been made (the ohlc one) — the volume
    # endpoint is never hit once we already know there's nothing to merge
    assert len(responses.calls) == 1
