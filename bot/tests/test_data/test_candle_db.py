"""Candle/scenario storage against SQLite (same SQLAlchemy code path as
Railway Postgres, apart from the dialect-specific upsert import)."""

from datetime import UTC, datetime

import pandas as pd
import pytest

from data.candle_db import (
    build_upsert,
    get_engine,
    latest_timestamp,
    load_candles,
    load_scenarios,
    normalize_url,
    save_scenario,
    upsert_candles,
)


@pytest.fixture
def engine(tmp_path):
    return get_engine(f"sqlite:///{tmp_path / 'candles.db'}")


def _frame(start: str, closes: list[float]) -> pd.DataFrame:
    ts = pd.date_range(start, periods=len(closes), freq="D", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": closes,
            "high": [c * 1.1 for c in closes],
            "low": [c * 0.9 for c in closes],
            "close": closes,
            "volume": [100.0] * len(closes),
        }
    )


def test_upsert_then_load_round_trips_with_utc_timestamps(engine):
    df = _frame("2026-10-01", [1.0, 2.0, 3.0])

    assert upsert_candles(engine, "coinbase", "AERO/USD", "1d", df) == 3
    loaded = load_candles(engine, "coinbase", "AERO/USD", "1d")

    assert len(loaded) == 3
    assert str(loaded["timestamp"].dt.tz) == "UTC"
    pd.testing.assert_series_equal(loaded["timestamp"], df["timestamp"], check_names=False)
    assert loaded["close"].tolist() == [1.0, 2.0, 3.0]


def test_overlapping_upsert_updates_instead_of_duplicating(engine):
    upsert_candles(engine, "coinbase", "AERO/USD", "1d", _frame("2026-10-01", [1.0, 2.0, 3.0]))
    # re-fetch of the last two days: day 3 was still forming the first time
    upsert_candles(engine, "coinbase", "AERO/USD", "1d", _frame("2026-10-02", [2.0, 3.5, 4.0]))

    loaded = load_candles(engine, "coinbase", "AERO/USD", "1d")

    assert loaded["close"].tolist() == [1.0, 2.0, 3.5, 4.0]
    assert loaded["timestamp"].is_unique


def test_series_are_isolated_by_exchange_symbol_and_timeframe(engine):
    upsert_candles(engine, "coinbase", "AERO/USD", "1d", _frame("2026-10-01", [1.0]))
    upsert_candles(engine, "coinbase", "BTC/USD", "1d", _frame("2026-10-01", [80_000.0]))
    upsert_candles(engine, "bitvavo", "AERO/USD", "1d", _frame("2026-10-01", [0.9]))

    assert load_candles(engine, "coinbase", "AERO/USD", "1d")["close"].tolist() == [1.0]
    assert load_candles(engine, "coinbase", "AERO/USD", "1w").empty


def test_latest_timestamp_and_since_filter(engine):
    assert latest_timestamp(engine, "coinbase", "AERO/USD", "1d") is None
    upsert_candles(engine, "coinbase", "AERO/USD", "1d", _frame("2026-10-01", [1.0, 2.0, 3.0]))

    assert latest_timestamp(engine, "coinbase", "AERO/USD", "1d") == pd.Timestamp("2026-10-03", tz="UTC")
    since = datetime(2026, 10, 2, tzinfo=UTC)
    assert load_candles(engine, "coinbase", "AERO/USD", "1d", since=since)["close"].tolist() == [2.0, 3.0]


def test_save_and_load_scenarios(engine):
    payload = {"price": 0.79, "state": "extended", "trigger": 1.0, "targets": [1.3, 1.58]}

    row_id = save_scenario(engine, "coinbase", "AERO/USD", "1w", payload)
    rows = load_scenarios(engine, symbol="AERO/USD")

    assert row_id == 1
    assert len(rows) == 1
    assert rows.iloc[0]["state"] == "extended"
    assert rows.iloc[0]["payload"]["targets"] == [1.3, 1.58]


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgresql://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("sqlite:///x.db", "sqlite:///x.db"),
    ],
)
def test_normalize_url(url, expected):
    assert normalize_url(url) == expected


def test_postgres_upsert_compiles_to_on_conflict_update():
    from sqlalchemy.dialects import postgresql

    record = {
        "exchange": "coinbase",
        "symbol": "AERO/USD",
        "timeframe": "1d",
        "ts": datetime(2026, 10, 1, tzinfo=UTC),
        "open": 1.0,
        "high": 1.1,
        "low": 0.9,
        "close": 1.0,
        "volume": 5.0,
    }
    sql = str(build_upsert("postgresql", [record]).compile(dialect=postgresql.dialect()))

    assert "ON CONFLICT (exchange, symbol, timeframe, ts) DO UPDATE" in sql
    assert "close = excluded.close" in sql


def test_get_engine_without_url_raises(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError):
        get_engine()
