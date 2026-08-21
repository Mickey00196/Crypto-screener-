"""Real Phase 1 data fetch: Binance (BTC/USDT, ETH/USDT — deep 3yr+ research
history) + Bitvavo (BTC/EUR, ETH/EUR — recent execution/paper-trading
history), validated, stored as Parquet, and split into
train/val/holdout via data/splits.py.

NOT RUN in this session: this sandbox's network egress is blocked to both
exchange APIs (403 policy denial at the proxy — confirmed via curl and the
proxy status log). This script is real and ready; run it once network
access exists. See bot/FINDINGS.md for the full explanation.

Run: python scripts/run_phase1_fetch.py
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from data.fetch_binance import fetch_binance_ohlcv
from data.fetch_bitvavo import fetch_bitvavo_ohlcv
from data.splits import build_holdout_config_from_storage
from data.storage import save_ohlcv
from data.validate import validate_ohlcv
from settings import DEFAULT_HOLDOUT_PATH, load_settings

RESEARCH_PAIRS_BINANCE = ["BTC/USDT", "ETH/USDT"]
EXECUTION_PAIRS_BITVAVO = ["BTC/EUR", "ETH/EUR"]
TIMEFRAMES = ["1h", "4h"]
RESEARCH_HISTORY_YEARS = 3
EXECUTION_HISTORY_DAYS = 90  # Bitvavo data here is for paper-trading/basis docs, not deep backtesting


def fetch_and_store(symbol: str, timeframe: str, since: datetime, source: str) -> None:
    print(f"Fetching {symbol}/{timeframe} from {source} since {since.date()}...")
    if source == "binance":
        df = fetch_binance_ohlcv(symbol, timeframe, since)
    elif source == "bitvavo":
        df = fetch_bitvavo_ohlcv(symbol, timeframe, since)
    else:
        raise ValueError(source)

    if df.empty:
        print(f"  WARNING: no data returned for {symbol}/{timeframe} from {source}")
        return

    clean_df, report = validate_ohlcv(df, timeframe)
    print(
        f"  {len(clean_df)} bars, {report.duplicates_removed} duplicates removed, "
        f"{len(report.gaps)} gap(s) totalling {report.total_missing_bars} missing bars"
    )
    save_ohlcv(clean_df, symbol, timeframe)


def main() -> None:
    settings = load_settings()
    research_since = datetime.now(UTC) - timedelta(days=365 * RESEARCH_HISTORY_YEARS)
    execution_since = datetime.now(UTC) - timedelta(days=EXECUTION_HISTORY_DAYS)

    for symbol in RESEARCH_PAIRS_BINANCE:
        for timeframe in TIMEFRAMES:
            fetch_and_store(symbol, timeframe, research_since, source="binance")

    for symbol in EXECUTION_PAIRS_BITVAVO:
        for timeframe in TIMEFRAMES:
            fetch_and_store(symbol, timeframe, execution_since, source="bitvavo")

    print("\nComputing chronological train/val/holdout splits from the Binance research history...")
    path = build_holdout_config_from_storage(
        symbols=RESEARCH_PAIRS_BINANCE,
        timeframes=TIMEFRAMES,
        train_frac=settings.train_frac,
        val_frac=settings.val_frac,
        output_path=DEFAULT_HOLDOUT_PATH,
    )
    print(f"Wrote holdout boundaries to {path}")


if __name__ == "__main__":
    main()
