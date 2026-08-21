# RESULTS

**There is no real-data result to report this session.** See `FINDINGS.md`
for the full explanation — this sandbox's network egress cannot reach
Binance or Bitvavo, so Phase 1's data fetch, Phase 4's real optimization
sweep and holdout evaluation, and Phase 5's live paper trading never ran.
Reporting fabricated numbers here to fill out a metrics table would be
exactly the failure mode the build brief's hard rules exist to prevent.

This document is a placeholder for what a real run produces, plus the one
thing that *did* run for real this session: a synthetic pipeline
correctness check. **Do not read the numbers below as evidence of strategy
quality** — that's the whole point of the label on every one of them.

## What actually ran: synthetic pipeline smoke test

`scripts/run_pipeline_smoketest.py`, on GBM-generated synthetic OHLCV
(`data/synthetic.py`, regime="mixed", ~3,200 bars/series, 2 series), all
rows tagged `[SYNTHETIC SMOKE TEST]` in `EXPERIMENTS.md`:

| Family | Configs run | Not overfit-rejected | Walk-forward (best candidate) | Definition-of-Done gates (validation) |
|---|---|---|---|---|
| TrendFilteredPullbackStrategy | 12 | 1 | 0/8 windows positive | FAIL (sortino, trade_count, walk-forward — only 1 trade total) |
| VolatilityBreakoutTrendStrategy | 12 | 0 | — no candidate survived overfit check — | — |
| TrendContinuationConfluenceStrategy | 12 | 11 | 2/8 windows positive | FAIL (trade_count=52 < 200, walk-forward 2 < 3 windows) — but win_rate/profit_factor/expectancy/drawdown/sortino all individually PASSED |

This is exactly the shape of result an honest small-sample smoke test
should produce: mostly rejected on overfit or thin-data gates, nothing
manufactured to look like a pass. It proves `data → engine → optimizer →
walk-forward → gates` executes correctly end to end — sampling is seeded
and bounded, costs are applied, the overfit check fires, walk-forward
windows generate and evaluate, and the gate checker correctly flags both
individual-metric failures and multi-window insufficiency. It proves
nothing about whether any of the three strategies has real edge on real
crypto markets.

## What a real run will fill in here

Once `scripts/run_phase1_fetch.py` has been run from an environment with
exchange API access (see `FINDINGS.md`), a real Phase 4 run produces, per
surviving candidate:

- Full metrics table: win rate, profit factor, expectancy, avg R:R,
  max drawdown, Sortino, trade count — train / validation / holdout,
  side by side.
- Walk-forward chart/table: pass/fail per window, ≥3 required.
- Regime breakdown: expectancy in bull vs. chop/bear sub-periods.
- Benchmark comparison: strategy Sortino vs. buy-and-hold Sortino over the
  same holdout window.
- An explicit "what would break this strategy" statement (per the brief's
  Phase 6 requirement) — e.g. a funding-rate regime shift, a sustained
  low-ADX chop period beyond what training data covered, a fee-schedule
  change, exchange downtime during a signal bar.

If no candidate clears every gate on real data, this section will instead
say so plainly and point to an updated `FINDINGS.md` — not be filled in
with the best-looking near-miss.

## Caveat carried over from RESEARCH.md

Even with real data, clearing win rate ≥55% **and** profit factor ≥1.3
**and** beating buy-and-hold risk-adjusted, simultaneously, is not
guaranteed — see `RESEARCH.md §1` for why that specific combination is
hard by construction. A negative real-data result would still be a
legitimate, useful outcome of this project, not a failure of it.
