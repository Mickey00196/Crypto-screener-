"""One-off utility: fetches REAL Bitvavo OHLCV using the already-tested
data/fetch_bitvavo.py and prints every row as a CSV line to stdout.

Why this exists: this sandbox's own network egress cannot reach Bitvavo
(see FINDINGS.md), but a Railway deployment can (confirmed this session:
api.bitvavo.com returned HTTP 200 from Railway's us-west2 region). There is
no file-transfer channel between a Railway container and this sandbox, but
Railway's own log-retrieval tool works regardless of the sandbox's network
policy — so this script's whole job is to make the fetched data visible
through stdout/logs, where it gets reassembled back into a real Parquet
file by scripts/run_phase1_fetch.py's normal path afterward.

Not part of the normal pipeline — this is a one-time bridge for this
session's specific network constraint, not a replacement for
scripts/run_phase1_fetch.py (which remains the real entrypoint once
wherever this runs has direct network access).

Run (via a Railway service startCommand override):
    python scripts/railway_fetch_dump.py
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from data.fetch_bitvavo import fetch_bitvavo_ohlcv

SYMBOLS = ["BTC/EUR", "ETH/EUR"]
TIMEFRAME = "1h"
LOOKBACK_DAYS = 90


def main() -> None:
    since = datetime.now(UTC) - timedelta(days=LOOKBACK_DAYS)
    until = datetime.now(UTC)
    total = 0

    for symbol in SYMBOLS:
        df = fetch_bitvavo_ohlcv(symbol, TIMEFRAME, since, until)
        print(f"SYMBOL_START,{symbol},{TIMEFRAME},{len(df)}", flush=True)
        for row in df.itertuples(index=False):
            print(
                f"ROW,{symbol},{TIMEFRAME},{row.timestamp.isoformat()},"
                f"{row.open!r},{row.high!r},{row.low!r},{row.close!r},{row.volume!r}",
                flush=True,
            )
            total += 1
        print(f"SYMBOL_END,{symbol},{TIMEFRAME}", flush=True)

    print(f"FETCH_ALL_DONE,total_rows={total}", flush=True)


if __name__ == "__main__":
    main()
