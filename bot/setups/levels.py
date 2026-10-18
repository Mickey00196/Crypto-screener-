"""Key horizontal levels: swing pivots clustered into price zones, plus the
nearest major round numbers (1-2-5 series: 0.5, 1, 2, 5, 10 ...).

Lookahead: a confirmed pivot needs `k` bars on its right, so the last `k`
bars can never hold one. The latest swing extreme is still something a
chart reader marks (AERO's fresh 1.00 high, say), so it is added as a
PROVISIONAL pivot when it is the extreme of everything from `k` bars before
it up to now — and never from the still-forming last bar."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
import pandas as pd

from indicators.structure import swing_high_low
from indicators.trend import atr

PivotKind = Literal["high", "low"]


@dataclass(frozen=True)
class Pivot:
    index: int
    timestamp: pd.Timestamp
    price: float
    kind: PivotKind
    provisional: bool = False


@dataclass(frozen=True)
class Level:
    price: float
    touches: int
    last_index: int
    score: float
    kinds: tuple[str, ...]
    is_round: bool = False
    provisional: bool = False

    def to_dict(self) -> dict:
        out = asdict(self)
        out["kinds"] = list(self.kinds)
        return out


def find_pivots(df: pd.DataFrame, k: int = 3) -> list[Pivot]:
    swings = swing_high_low(df, k)
    ts = df["timestamp"]
    pivots = [
        Pivot(int(i), ts.iloc[i], float(df["high"].iloc[i]), "high")
        for i in np.flatnonzero(swings["swing_high"].to_numpy())
    ] + [
        Pivot(int(i), ts.iloc[i], float(df["low"].iloc[i]), "low")
        for i in np.flatnonzero(swings["swing_low"].to_numpy())
    ]

    n = len(df)
    if n > 2 * k + 1:
        # candidates: the last k bars except the forming one
        tail = range(n - k, n - 1)
        hi = max(tail, key=lambda i: df["high"].iloc[i])
        if df["high"].iloc[hi] >= df["high"].iloc[hi - k : n].max():
            pivots.append(Pivot(hi, ts.iloc[hi], float(df["high"].iloc[hi]), "high", provisional=True))
        lo = min(tail, key=lambda i: df["low"].iloc[i])
        if df["low"].iloc[lo] <= df["low"].iloc[lo - k : n].min():
            pivots.append(Pivot(lo, ts.iloc[lo], float(df["low"].iloc[lo]), "low", provisional=True))

    return sorted(pivots, key=lambda p: p.index)


def auto_tolerance(df: pd.DataFrame, period: int = 14, window: int = 52) -> float:
    """Half the typical candle range as a fraction of price, clamped to
    2-8%. Levels closer together than this are treated as one zone."""
    rel = (atr(df, period) / df["close"]).dropna().tail(window)
    if rel.empty:
        return 0.04
    return float(np.clip(0.5 * rel.median(), 0.02, 0.08))


def round_levels(price: float) -> tuple[float, float]:
    """Nearest 1-2-5 series numbers below and above `price`
    (0.79 -> 0.5 / 1.0, 81_550 -> 50_000 / 100_000)."""
    if price <= 0:
        raise ValueError("price must be positive")
    exp = math.floor(math.log10(price))
    series = [m * 10.0**e for e in (exp - 1, exp, exp + 1) for m in (1, 2, 5)]
    below = max(x for x in series if x <= price)
    above = min(x for x in series if x > price)
    return below, above


def cluster_pivots(
    pivots: list[Pivot], tolerance: float, now_index: int, halflife: float = 26.0
) -> list[Level]:
    """Greedy clustering on sorted prices: a pivot joins the current cluster
    while it sits within `tolerance` (fractional) of the cluster's lowest
    price. Score rewards repeated and recent touches."""
    levels: list[Level] = []
    cluster: list[Pivot] = []

    def flush():
        if not cluster:
            return
        prices = [p.price for p in cluster]
        recency = sum(0.5 ** ((now_index - p.index) / halflife) for p in cluster)
        levels.append(
            Level(
                price=float(np.median(prices)),
                touches=len(cluster),
                last_index=max(p.index for p in cluster),
                score=recency + 0.25 * len(cluster),
                kinds=tuple(sorted({p.kind for p in cluster})),
                provisional=all(p.provisional for p in cluster),
            )
        )

    for p in sorted(pivots, key=lambda p: p.price):
        if cluster and p.price > cluster[0].price * (1 + tolerance):
            flush()
            cluster = []
        cluster.append(p)
    flush()
    return levels


def build_levels(
    df: pd.DataFrame,
    pivots: list[Pivot],
    tolerance: float,
    max_levels: int = 10,
    halflife: float = 52.0,
    keep_above: int = 3,
    keep_below: int = 2,
) -> list[Level]:
    """Top `max_levels` levels by score, always keeping the nearest
    `keep_above` levels above price (trigger + two targets) and `keep_below`
    below; returned sorted by price."""
    now = len(df) - 1
    price = float(df["close"].iloc[-1])
    levels = cluster_pivots(pivots, tolerance, now, halflife)

    for rnd in round_levels(price):
        match = next((lv for lv in levels if abs(lv.price / rnd - 1) <= tolerance), None)
        if match is not None:
            levels[levels.index(match)] = Level(
                **{**match.__dict__, "is_round": True, "score": match.score + 0.5}
            )
        else:
            levels.append(Level(rnd, 0, now, 0.5, (), is_round=True))

    keep = set(sorted(range(len(levels)), key=lambda i: levels[i].score, reverse=True)[:max_levels])
    below = sorted((i for i, lv in enumerate(levels) if lv.price < price), key=lambda i: -levels[i].price)
    above = sorted((i for i, lv in enumerate(levels) if lv.price > price), key=lambda i: levels[i].price)
    keep.update(below[:keep_below])
    keep.update(above[:keep_above])
    return sorted((levels[i] for i in keep), key=lambda lv: lv.price)
