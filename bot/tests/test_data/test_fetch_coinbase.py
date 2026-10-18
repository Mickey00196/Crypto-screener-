"""Coinbase windowed fetch + weekly resampling, tested against a fake
exchange (this sandbox cannot reach api.exchange.coinbase.com)."""

from datetime import UTC, datetime

import pandas as pd
import pytest

from data.fetch_coinbase import fetch_coinbase_ohlcv, fetch_windowed_history
from data.resample import resample_ohlcv

DAY_MS = 86_400_000
BASE = 1_700_006_400_000  # 2023-11-15 00:00 UTC


class WindowedFakeExchange:
    """Mimics Coinbase: returns at most `limit` daily candles starting at
    `since`, and nothing before `listed_ms` or at/after `now_ms`."""

    def __init__(self, listed_ms: int, now_ms: int):
        self.listed_ms = listed_ms
        self.now_ms = now_ms
        self.calls: list[int] = []

    def parse_timeframe(self, timeframe):
        return 86_400

    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        self.calls.append(since)
        rows = []
        for i in range(limit):
            ts = since + i * DAY_MS
            if self.listed_ms <= ts < self.now_ms:
                rows.append([ts, 1.0, 2.0, 0.5, 1.5, 10.0])
        return rows


def test_skips_empty_windows_before_listing():
    listed = BASE + 700 * DAY_MS
    now = BASE + 1000 * DAY_MS
    exchange = WindowedFakeExchange(listed_ms=listed, now_ms=now)

    df = fetch_windowed_history(exchange, "AERO/USD", "1d", BASE, now, limit=300)

    # windows 0-299 and 300-599 are empty (pre-listing) but must not stop the walk
    assert len(df) == 300
    assert df["timestamp"].min() == pd.to_datetime(listed, unit="ms", utc=True)
    assert len(exchange.calls) == 4  # 1000 days / 300-day windows


def test_until_is_exclusive_and_rows_are_unique_and_sorted():
    now = BASE + 50 * DAY_MS
    exchange = WindowedFakeExchange(listed_ms=BASE, now_ms=BASE + 10_000 * DAY_MS)

    df = fetch_windowed_history(exchange, "AERO/USD", "1d", BASE, now, limit=7)

    assert len(df) == 50
    assert df["timestamp"].max() < pd.to_datetime(now, unit="ms", utc=True)
    assert df["timestamp"].is_monotonic_increasing and df["timestamp"].is_unique
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]


def test_unaligned_since_is_floored_to_the_candle_boundary():
    exchange = WindowedFakeExchange(listed_ms=BASE, now_ms=BASE + 30 * DAY_MS)
    since = BASE + 10 * 3_600_000  # 10:00 on the first day

    df = fetch_windowed_history(exchange, "AERO/USD", "1d", since, BASE + 5 * DAY_MS, limit=300)

    assert exchange.calls[0] == BASE
    assert df["timestamp"].min() == pd.to_datetime(BASE, unit="ms", utc=True)
    assert len(df) == 5


def test_empty_range_returns_empty_frame():
    exchange = WindowedFakeExchange(listed_ms=BASE, now_ms=BASE + DAY_MS)
    assert fetch_windowed_history(exchange, "AERO/USD", "1d", BASE, BASE).empty
    assert exchange.calls == []


def test_fetch_coinbase_ohlcv_accepts_datetimes():
    exchange = WindowedFakeExchange(listed_ms=BASE, now_ms=BASE + 30 * DAY_MS)
    since = datetime.fromtimestamp(BASE / 1000, tz=UTC)
    until = datetime.fromtimestamp((BASE + 10 * DAY_MS) / 1000, tz=UTC)

    df = fetch_coinbase_ohlcv("AERO/USD", "1d", since, until, exchange=exchange)

    assert len(df) == 10


def test_weekly_resample_starts_monday_and_aggregates_correctly():
    days = pd.date_range("2026-10-05", periods=14, freq="D", tz="UTC")  # Mon 5 Oct .. Sun 18 Oct
    df = pd.DataFrame(
        {
            "timestamp": days,
            "open": range(1, 15),
            "high": [x + 0.5 for x in range(1, 15)],
            "low": [x - 0.5 for x in range(1, 15)],
            "close": [x + 0.25 for x in range(1, 15)],
            "volume": [1.0] * 14,
        }
    )

    weekly = resample_ohlcv(df, "1w")

    assert list(weekly["timestamp"]) == [
        pd.Timestamp("2026-10-05", tz="UTC"),
        pd.Timestamp("2026-10-12", tz="UTC"),
    ]
    first = weekly.iloc[0]
    assert (first.open, first.high, first.low, first.close, first.volume) == (1, 7.5, 0.5, 7.25, 7.0)


def test_resample_rejects_unknown_timeframe():
    with pytest.raises(ValueError):
        resample_ohlcv(pd.DataFrame(), "3h")
