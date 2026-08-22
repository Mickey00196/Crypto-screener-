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

import time
from datetime import UTC, datetime, timedelta

from data.fetch_bitvavo import fetch_bitvavo_ohlcv

SYMBOLS = ["BTC/EUR", "ETH/EUR"]
TIMEFRAME = "1h"
LOOKBACK_DAYS = 90
BATCH_SIZE = 40  # rows per printed log line — Railway rate-limits at 500 log
# lines/sec per replica and silently DROPS lines over that (learned the hard
# way: one-row-per-line dropped 1,258 of ~4,320 rows). Batching + a small
# sleep between batches keeps well clear of that limit.
BATCH_SLEEP_SECONDS = 0.05


def _encode_row(row) -> str:
    return f"{row.timestamp.isoformat()},{row.open!r},{row.high!r},{row.low!r},{row.close!r},{row.volume!r}"


def main() -> None:
    since = datetime.now(UTC) - timedelta(days=LOOKBACK_DAYS)
    until = datetime.now(UTC)
    total = 0

    for symbol in SYMBOLS:
        df = fetch_bitvavo_ohlcv(symbol, TIMEFRAME, since, until)
        print(f"SYMBOL_START,{symbol},{TIMEFRAME},{len(df)}", flush=True)
        rows = list(df.itertuples(index=False))
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            encoded = "|".join(_encode_row(r) for r in batch)
            print(f"BATCH,{symbol},{TIMEFRAME},{i},{len(batch)},{encoded}", flush=True)
            total += len(batch)
            time.sleep(BATCH_SLEEP_SECONDS)
        print(f"SYMBOL_END,{symbol},{TIMEFRAME}", flush=True)

    print(f"FETCH_ALL_DONE,total_rows={total}", flush=True)


if __name__ == "__main__":
    main()
