"""Lookahead detector: proves (or disproves) that a strategy's signal for
bar t depends only on data through bar t's close. Required by the hard rule
that a lookahead-introducing bug must be automatically catchable."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


class LookaheadError(Exception):
    """Raised when a strategy's signal at some bar t differs depending on
    whether it saw data beyond bar t — i.e. it is using future information."""


@dataclass
class LookaheadReport:
    passed: bool
    checked_bars: int
    first_offending_index: int | None = None


def detect_lookahead(strategy, df: pd.DataFrame, warmup: int = 5) -> LookaheadReport:
    """For each bar t (after `warmup` bars), compares the signal produced by
    running generate_signals on the FULL dataframe against the signal
    produced by running it on ONLY data through bar t (df.iloc[:t+1]). Any
    mismatch means the strategy peeked at bars after t to produce t's signal,
    and raises LookaheadError naming the offending index."""
    if len(df) <= warmup:
        raise ValueError(f"need more than warmup={warmup} bars to run a lookahead check")

    full_signals = strategy.generate_signals(df).reset_index(drop=True)
    n = len(df)

    for t in range(warmup, n):
        truncated_signals = strategy.generate_signals(df.iloc[: t + 1]).reset_index(drop=True)
        full_val = full_signals.iloc[t]
        truncated_val = truncated_signals.iloc[-1]

        full_is_na = pd.isna(full_val)
        truncated_is_na = pd.isna(truncated_val)
        mismatch = (full_is_na != truncated_is_na) or (
            not full_is_na and not truncated_is_na and full_val != truncated_val
        )
        if mismatch:
            raise LookaheadError(
                f"lookahead detected at bar index {t}: signal computed with the full "
                f"dataframe ({full_val!r}) differs from the signal computed using only "
                f"data through bar {t} ({truncated_val!r}). The strategy is using "
                "information beyond that bar's close to produce that bar's signal."
            )

    return LookaheadReport(passed=True, checked_bars=n - warmup)
