"""End-to-end scan against SQLite with a fake fetcher that serves daily
candles which resample exactly to the AERO weekly fixture."""

from datetime import timedelta

import pandas as pd
import pytest
import responses

from data.candle_db import get_engine, load_candles, load_scenarios
from setups.notify import TELEGRAM_API, send_telegram
from setups.scan import parse_symbols, run_scan
from tests.test_setups.series import aero_like


def weekly_to_daily(weekly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for w in weekly.itertuples(index=False):
        o, h, lo, c = w.open, w.high, w.low, w.close
        for d in range(7):
            close = c if d == 6 else o
            rows.append(
                {
                    "timestamp": w.timestamp + timedelta(days=d),
                    "open": o,
                    "high": h if d == 1 else max(o, close),
                    "low": lo if d == 2 else min(o, close),
                    "close": close,
                    "volume": w.volume / 7,
                }
            )
    return pd.DataFrame(rows)


class FakeFetcher:
    def __init__(self, daily: pd.DataFrame):
        self.daily = daily
        self.calls: list[tuple] = []

    def __call__(self, symbol, timeframe, since, until):
        self.calls.append((symbol, timeframe, since, until))
        ts = self.daily["timestamp"]
        return self.daily[(ts >= pd.Timestamp(since)) & (ts < pd.Timestamp(until))].reset_index(drop=True)


@pytest.fixture
def aero_daily():
    return weekly_to_daily(aero_like())


@pytest.fixture
def now(aero_daily):
    return (aero_daily["timestamp"].max() + timedelta(days=1)).to_pydatetime()


def test_daily_fixture_resamples_back_to_the_weekly_series(aero_daily):
    from data.resample import resample_ohlcv

    weekly = resample_ohlcv(aero_daily, "1w")
    expected = aero_like()
    pd.testing.assert_frame_equal(
        weekly[["open", "high", "low", "close"]], expected[["open", "high", "low", "close"]], check_freq=False
    )


def test_scan_with_database_stores_candles_logs_scenario_and_refetches_incrementally(
    tmp_path, aero_daily, now
):
    engine = get_engine(f"sqlite:///{tmp_path / 'scan.db'}")
    fetch = FakeFetcher(aero_daily)

    [(exchange, symbol, setup)] = run_scan(
        [("coinbase", "AERO/USD")], engine=engine, fetchers={"coinbase": fetch}, now=now, lookback_days=500
    )

    assert (exchange, symbol) == ("coinbase", "AERO/USD")
    assert setup.state == "extended" and setup.trigger == pytest.approx(1.0)
    assert len(load_candles(engine, "coinbase", "AERO/USD", "1d")) == len(aero_daily)
    assert fetch.calls[0][2] == now - timedelta(days=500)

    run_scan(
        [("coinbase", "AERO/USD")], engine=engine, fetchers={"coinbase": fetch}, now=now, lookback_days=500
    )

    # second run only re-fetches the last few days and doesn't duplicate rows
    second_since = pd.Timestamp(fetch.calls[1][2])
    assert second_since == aero_daily["timestamp"].max() - timedelta(days=3)
    assert len(load_candles(engine, "coinbase", "AERO/USD", "1d")) == len(aero_daily)
    scenarios = load_scenarios(engine, symbol="AERO/USD")
    assert len(scenarios) == 2 and set(scenarios["state"]) == {"extended"}


def test_scan_without_database_fetches_full_lookback(aero_daily, now):
    fetch = FakeFetcher(aero_daily)

    [(_, _, setup)] = run_scan([("coinbase", "AERO/USD")], fetchers={"coinbase": fetch}, now=now)

    assert setup.state == "extended"
    assert len(fetch.calls) == 1


def test_one_failing_symbol_does_not_stop_the_scan(aero_daily, now):
    def broken(symbol, timeframe, since, until):
        raise ConnectionError("exchange down")

    results = run_scan(
        [("coinbase", "AERO/USD"), ("bitvavo", "AERO/EUR"), ("kraken", "AERO/USD")],
        fetchers={"coinbase": FakeFetcher(aero_daily), "bitvavo": broken},
        now=now,
    )

    outcomes = {f"{ex}:{sym}": type(res).__name__ for ex, sym, res in results}
    assert outcomes == {
        "coinbase:AERO/USD": "Setup",
        "bitvavo:AERO/EUR": "ConnectionError",
        "kraken:AERO/USD": "ValueError",
    }


def test_retry_wrapper_is_unwrapped_to_the_exchange_error(now):
    from tenacity import retry, stop_after_attempt

    @retry(stop=stop_after_attempt(2))
    def flaky(symbol, timeframe, since, until):
        raise TimeoutError("coinbase timed out")

    [(_, _, result)] = run_scan([("coinbase", "AERO/USD")], fetchers={"coinbase": flaky}, now=now)

    assert isinstance(result, TimeoutError)


def test_empty_fetch_is_reported_as_error(now):
    empty = FakeFetcher(pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"]))
    [(_, _, result)] = run_scan([("coinbase", "NEW/USD")], fetchers={"coinbase": empty}, now=now)

    assert isinstance(result, ValueError)


def test_parse_symbols():
    assert parse_symbols(" coinbase:aero/usd, bitvavo:BTC/EUR ,") == [
        ("coinbase", "AERO/USD"),
        ("bitvavo", "BTC/EUR"),
    ]
    with pytest.raises(ValueError):
        parse_symbols("AERO/USD")


@responses.activate
def test_send_telegram_posts_and_splits_long_messages():
    url = f"{TELEGRAM_API}/botTOKEN/sendMessage"
    responses.add(responses.POST, url, json={"ok": True}, status=200)
    text = "\n\n".join(["x" * 3000, "y" * 3000, "z" * 10])

    sent = send_telegram(text, "TOKEN", "42")

    assert sent == 2
    bodies = [call.request.body for call in responses.calls]
    assert all(b'"chat_id": "42"' in b for b in bodies)
