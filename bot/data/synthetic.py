"""SYNTHETIC DATA GENERATOR — for pipeline smoke-testing only.

Produces GBM-based OHLCV bars with an injected regime structure (trend_up,
trend_down, chop/mean-reverting, or a mixed sequence of blocks). This is NOT
real market data and must NEVER be used to draw conclusions about strategy
quality or to satisfy the Definition of Done — only to verify that the
data -> engine -> optimizer -> gates -> evaluation pipeline executes
correctly end to end. Every consumer of this module (scripts/
run_pipeline_smoketest.py, EXPERIMENTS.md rows) must tag output
"[SYNTHETIC SMOKE TEST]".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_FREQ_MAP = {"5m": "5min", "15m": "15min", "1h": "h", "4h": "4h"}


def generate_deterministic_trend(
    n_bars: int = 500,
    timeframe: str = "1h",
    start: str = "2022-01-01",
    start_price: float = 20000.0,
    pct_per_bar: float = 0.002,
    direction: str = "up",
) -> pd.DataFrame:
    """Deterministic, noise-free monotonic trend — NOT for strategy
    evaluation (see generate_synthetic_ohlcv for the noisy regime generator
    used in the Phase 4 pipeline smoke test). This exists only for
    backtest-engine sanity tests (Phase 2) that need a guaranteed-monotonic
    uptrend/downtrend regardless of random seed, per the brief's "synthetic
    constant uptrend" test requirement."""
    if direction not in {"up", "down"}:
        raise ValueError("direction must be 'up' or 'down'")
    if timeframe not in _FREQ_MAP:
        raise ValueError(f"unsupported timeframe {timeframe!r}")

    timestamps = pd.date_range(start=start, periods=n_bars, freq=_FREQ_MAP[timeframe], tz="UTC")
    sign = 1 if direction == "up" else -1
    factor = 1 + sign * pct_per_bar
    closes = start_price * (factor ** np.arange(1, n_bars + 1))
    opens = np.empty(n_bars)
    opens[0] = start_price
    opens[1:] = closes[:-1]
    highs = np.maximum(opens, closes)
    lows = np.minimum(opens, closes)
    volumes = np.full(n_bars, 100.0)

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }
    )


def generate_synthetic_ohlcv(
    n_bars: int = 2000,
    timeframe: str = "1h",
    regime: str = "mixed",
    seed: int = 42,
    start: str = "2022-01-01",
    start_price: float = 20000.0,
) -> pd.DataFrame:
    if timeframe not in _FREQ_MAP:
        raise ValueError(f"unsupported timeframe {timeframe!r}")
    if regime not in {"trend_up", "trend_down", "chop", "mixed", "zero_vol"}:
        raise ValueError(f"unsupported regime {regime!r}")

    rng = np.random.default_rng(seed)
    timestamps = pd.date_range(start=start, periods=n_bars, freq=_FREQ_MAP[timeframe], tz="UTC")

    if regime == "zero_vol":
        closes = np.full(n_bars, start_price)
        opens = closes.copy()
        highs = closes.copy()
        lows = closes.copy()
        volumes = np.zeros(n_bars)
        return pd.DataFrame(
            {
                "timestamp": timestamps,
                "open": opens,
                "high": highs,
                "low": lows,
                "close": closes,
                "volume": volumes,
            }
        )

    if regime == "mixed":
        block = max(n_bars // 4, 1)
        regimes = (
            ["trend_up"] * block
            + ["chop"] * block
            + ["trend_down"] * block
            + ["trend_up"] * (n_bars - 3 * block)
        )
    else:
        regimes = [regime] * n_bars

    closes = np.empty(n_bars)
    price = start_price
    ou_level = start_price
    sigma = 0.01
    for i, r in enumerate(regimes):
        if r == "trend_up":
            mu = 0.0006
            price *= np.exp((mu - 0.5 * sigma**2) + sigma * rng.standard_normal())
        elif r == "trend_down":
            mu = -0.0006
            price *= np.exp((mu - 0.5 * sigma**2) + sigma * rng.standard_normal())
        else:  # chop: mean-reverting (Ornstein-Uhlenbeck-ish) around a slowly drifting level
            theta = 0.05
            ou_level *= np.exp(0.00005 * rng.standard_normal())
            price += theta * (ou_level - price) + price * sigma * rng.standard_normal()
        closes[i] = max(price, 1e-6)

    opens = np.empty(n_bars)
    opens[0] = start_price
    opens[1:] = closes[:-1]
    intrabar_noise = np.abs(rng.standard_normal(n_bars)) * 0.003
    highs = np.maximum(opens, closes) * (1 + intrabar_noise)
    lows = np.minimum(opens, closes) * (1 - intrabar_noise)
    volumes = rng.lognormal(mean=5, sigma=0.5, size=n_bars)

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }
    )
