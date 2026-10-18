"""Postgres candle storage for the setup scanner (Railway Postgres in
production, SQLite in tests).

Two tables:
  - candles:   OHLCV keyed by (exchange, symbol, timeframe, ts); writes are
               upserts, so re-fetching an overlapping range is safe.
  - scenarios: one row per scan per symbol — the setup the scanner saw that
               day (state, zone, trigger, targets, invalidation) as JSON.
               This is the log to score later: did price do what the setup
               said, and how often?

Separate from data/storage.py on purpose: that module stores the research
Parquet splits behind the holdout guard; this one is the live scanner's
rolling store and never feeds backtest evaluation."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import pandas as pd
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Engine,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    func,
    select,
)

metadata = MetaData()

candles = Table(
    "candles",
    metadata,
    Column("exchange", String(32), primary_key=True),
    Column("symbol", String(32), primary_key=True),
    Column("timeframe", String(8), primary_key=True),
    Column("ts", DateTime(timezone=True), primary_key=True),
    Column("open", Float, nullable=False),
    Column("high", Float, nullable=False),
    Column("low", Float, nullable=False),
    Column("close", Float, nullable=False),
    Column("volume", Float, nullable=False),
)

scenarios = Table(
    "scenarios",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_at", DateTime(timezone=True), nullable=False),
    Column("exchange", String(32), nullable=False),
    Column("symbol", String(32), nullable=False),
    Column("timeframe", String(8), nullable=False),
    Column("price", Float, nullable=False),
    Column("state", String(32), nullable=False),
    Column("payload", JSON, nullable=False),
)

_OHLCV = ["open", "high", "low", "close", "volume"]
_KEY = ["exchange", "symbol", "timeframe", "ts"]
_CHUNK = 500


def normalize_url(url: str) -> str:
    """Railway exposes DATABASE_URL as postgres:// or postgresql://;
    SQLAlchemy needs the psycopg (v3) driver named explicitly."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


def get_engine(url: str | None = None) -> Engine:
    url = url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("no database URL: pass one or set DATABASE_URL")
    engine = create_engine(normalize_url(url), pool_pre_ping=True)
    metadata.create_all(engine)
    return engine


def build_upsert(dialect_name: str, records: list[dict[str, Any]]):
    """INSERT ... ON CONFLICT (exchange, symbol, timeframe, ts) DO UPDATE."""
    if dialect_name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif dialect_name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        raise NotImplementedError(f"upsert not implemented for {dialect_name}")
    stmt = insert(candles).values(records)
    return stmt.on_conflict_do_update(index_elements=_KEY, set_={col: stmt.excluded[col] for col in _OHLCV})


def upsert_candles(engine: Engine, exchange: str, symbol: str, timeframe: str, df: pd.DataFrame) -> int:
    """Insert or update candles; returns the number of rows written."""
    if df.empty:
        return 0
    timestamps = pd.to_datetime(df["timestamp"], utc=True)
    records = [
        {
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": timeframe,
            "ts": ts.to_pydatetime(),
            **{col: float(row[col]) for col in _OHLCV},
        }
        for ts, (_, row) in zip(timestamps, df.iterrows(), strict=True)
    ]
    with engine.begin() as conn:
        for i in range(0, len(records), _CHUNK):
            conn.execute(build_upsert(engine.dialect.name, records[i : i + _CHUNK]))
    return len(records)


def load_candles(
    engine: Engine, exchange: str, symbol: str, timeframe: str, since: datetime | None = None
) -> pd.DataFrame:
    query = select(candles.c.ts, *(candles.c[col] for col in _OHLCV)).where(
        candles.c.exchange == exchange, candles.c.symbol == symbol, candles.c.timeframe == timeframe
    )
    if since is not None:
        query = query.where(candles.c.ts >= since)
    with engine.connect() as conn:
        rows = conn.execute(query.order_by(candles.c.ts)).all()
    df = pd.DataFrame(rows, columns=["timestamp", *_OHLCV])
    if not df.empty:
        # SQLite drops tzinfo on the way out; everything is stored as UTC.
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def latest_timestamp(engine: Engine, exchange: str, symbol: str, timeframe: str) -> pd.Timestamp | None:
    query = select(func.max(candles.c.ts)).where(
        candles.c.exchange == exchange, candles.c.symbol == symbol, candles.c.timeframe == timeframe
    )
    with engine.connect() as conn:
        value = conn.execute(query).scalar()
    if value is None:
        return None
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def save_scenario(
    engine: Engine,
    exchange: str,
    symbol: str,
    timeframe: str,
    payload: dict[str, Any],
    run_at: datetime | None = None,
) -> int:
    row = {
        "run_at": run_at or datetime.now(UTC),
        "exchange": exchange,
        "symbol": symbol,
        "timeframe": timeframe,
        "price": float(payload["price"]),
        "state": str(payload["state"]),
        "payload": payload,
    }
    with engine.begin() as conn:
        result = conn.execute(scenarios.insert().values(**row))
    return int(result.inserted_primary_key[0])


def load_scenarios(engine: Engine, symbol: str | None = None) -> pd.DataFrame:
    query = select(scenarios).order_by(scenarios.c.run_at)
    if symbol is not None:
        query = query.where(scenarios.c.symbol == symbol)
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()
    return pd.DataFrame(rows)
