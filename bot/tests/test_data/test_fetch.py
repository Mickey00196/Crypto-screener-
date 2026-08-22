"""Unit tests for the ccxt pagination logic against a FAKE exchange — this
sandbox has no network egress to Binance/Bitvavo (see bot/FINDINGS.md), so
correctness of the fetch pipeline is proven here via dependency injection
rather than a live call."""

import pandas as pd

from data.exchange_fetch import fetch_ohlcv_history


class FakeExchange:
    def __init__(self, pages, tf_seconds=3600):
        self.pages = pages
        self.tf_seconds = tf_seconds
        self.calls: list[int] = []

    def parse_timeframe(self, timeframe):
        return self.tf_seconds

    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        self.calls.append(since)
        idx = len(self.calls) - 1
        return self.pages[idx] if idx < len(self.pages) else []


def _row(ts_ms, price=100.0):
    return [ts_ms, price, price, price, price, 1.0]


def test_pagination_stitches_pages_and_dedupes_overlap():
    base = 1_700_000_000_000
    hour = 3_600_000
    page1 = [_row(base + i * hour) for i in range(3)]
    page2 = [_row(base + (2 + i) * hour) for i in range(3)]  # overlaps last row of page1
    exchange = FakeExchange([page1, page2, []])

    df = fetch_ohlcv_history(exchange, "BTC/USDT", "1h", since_ms=base, limit=3)

    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert len(df) == 5  # 3 + 3 - 1 overlapping row
    assert df["timestamp"].is_monotonic_increasing
    assert df["timestamp"].is_unique


def test_until_ms_cutoff_is_respected():
    base = 1_700_000_000_000
    hour = 3_600_000
    page1 = [_row(base + i * hour) for i in range(5)]
    exchange = FakeExchange([page1, []])
    until = base + 2 * hour

    df = fetch_ohlcv_history(exchange, "BTC/USDT", "1h", since_ms=base, until_ms=until)

    assert df["timestamp"].max() < pd.to_datetime(until, unit="ms", utc=True)
    assert len(df) == 2


def test_short_page_before_until_ms_does_not_stop_pagination_early():
    """Regression test for a real bug found via a production Bitvavo fetch
    (see FINDINGS.md): a page returning fewer than `limit` rows must NOT be
    treated as "no more data" when there's still range left before an
    explicit until_ms — Bitvavo, confirmed, returns short pages mid-history,
    which silently truncated a requested 90-day fetch to ~42 days."""
    base = 1_700_000_000_000
    hour = 3_600_000
    page1 = [_row(base + i * hour) for i in range(3)]  # short page: 3 < limit(10)
    page2 = [_row(base + (3 + i) * hour) for i in range(3)]
    exchange = FakeExchange([page1, page2, []])
    until = base + 10 * hour

    df = fetch_ohlcv_history(exchange, "BTC/USDT", "1h", since_ms=base, until_ms=until, limit=10)

    assert len(df) == 6  # both pages fetched, not just page1's short 3 rows
    assert len(exchange.calls) >= 2


def test_short_page_with_no_until_ms_still_stops_early():
    """Without an explicit until_ms (open-ended "fetch to now"), a short
    page IS a reasonable signal that we've reached the end of history —
    this shortcut should still apply in that case."""
    base = 1_700_000_000_000
    hour = 3_600_000
    page1 = [_row(base + i * hour) for i in range(3)]  # short page: 3 < limit(10)
    exchange = FakeExchange([page1])

    df = fetch_ohlcv_history(exchange, "BTC/USDT", "1h", since_ms=base, limit=10)

    assert len(df) == 3
    assert len(exchange.calls) == 1


def test_empty_first_page_returns_empty_dataframe():
    exchange = FakeExchange([[]])
    df = fetch_ohlcv_history(exchange, "BTC/USDT", "1h", since_ms=1_700_000_000_000)
    assert df.empty


def test_stalled_pagination_terminates_instead_of_looping_forever():
    # exchange returns the exact same page forever (a misbehaving/mocked API) —
    # next_cursor would never advance past `cursor`, so the loop must break.
    base = 1_700_000_000_000
    stalled_page = [_row(base)]

    class StalledExchange:
        def parse_timeframe(self, timeframe):
            return 3600

        def fetch_ohlcv(self, symbol, timeframe, since, limit):
            return stalled_page

    df = fetch_ohlcv_history(StalledExchange(), "BTC/USDT", "1h", since_ms=base, max_pages=5)
    assert len(df) == 1
