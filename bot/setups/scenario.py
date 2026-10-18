"""Turn levels + channel into a trade-plan scenario — the rules behind the
"sweep, reclaim, break out" charts this scanner was modelled on.

Base: from the channel anchor (lowest swing low) to the last confirmed swing
low; base_high is the highest high in that window.

States:
  in_base          price is still inside the structure. Watch for a sweep
                   into the zone around the channel's lower line, then a
                   close above base_high (the trigger).
  extended         a closed candle broke above base_high; price is above the
                   retest zone (old base top / channel top).
  retesting        broke out, now back in the retest zone.
  failed_breakout  broke out, then fell back below the retest zone.
  breakdown        never broke out and is now below the base low.
  no_structure     no rising channel in the lookback window.

Breakouts are confirmed on CLOSED candles only: the last candle is treated
as still forming unless last_bar_complete=True. This is a description of a
chart, not a forecast; the scenario log in data/candle_db.py is how its hit
rate gets measured."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from setups.channel import Channel, fit_rising_channel
from setups.levels import Level, auto_tolerance, build_levels, find_pivots

STATE_TEXT = {
    "in_base": "Inside the base. Watch for a sweep into the zone, then a close above the trigger.",
    "extended": "Broke out of the base and is above the retest zone.",
    "retesting": "Broke out and is back in the retest zone (old base top / channel top).",
    "failed_breakout": "Broke out, then fell back below the retest zone. Breakout failed.",
    "breakdown": "Never broke out and is now below the base low.",
    "no_structure": "No rising channel in the lookback window.",
}


@dataclass
class Setup:
    symbol: str
    timeframe: str
    as_of: str
    price: float
    state: str
    tolerance: float
    base_low: float | None = None
    base_high: float | None = None
    breakout_at: str | None = None
    measured_move: float | None = None
    measured_move_hit: bool | None = None
    channel_lower: float | None = None
    channel_upper: float | None = None
    zone: tuple[float, float] | None = None
    zone_kind: str | None = None
    trigger: float | None = None
    targets: list[float] = field(default_factory=list)
    invalidation: float | None = None
    at_level: float | None = None
    supports: list[float] = field(default_factory=list)
    resistances: list[float] = field(default_factory=list)
    levels: list[Level] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out = {k: v for k, v in self.__dict__.items() if k != "levels"}
        out["zone"] = list(self.zone) if self.zone else None
        out["levels"] = [lv.to_dict() for lv in self.levels]
        return out


def analyze(
    df: pd.DataFrame,
    symbol: str = "",
    timeframe: str = "1w",
    k: int = 3,
    lookback: int = 52,
    tolerance: float | None = None,
    last_bar_complete: bool = False,
) -> Setup:
    if len(df) < 2 * k + 3:
        raise ValueError(f"need at least {2 * k + 3} candles, got {len(df)}")
    df = df.reset_index(drop=True)
    n = len(df)
    price = float(df["close"].iloc[-1])
    tol = tolerance if tolerance is not None else auto_tolerance(df)

    pivots = find_pivots(df, k)
    levels = build_levels(df, pivots, tol)
    prices = [lv.price for lv in levels]
    supports = sorted((p for p in prices if p < price * (1 - tol / 2)), reverse=True)
    resistances = sorted(p for p in prices if p > price * (1 + tol / 2))
    at_level = next((p for p in prices if abs(p / price - 1) <= tol / 2), None)

    def above(x: float) -> list[float]:
        return sorted(p for p in prices if p > x * (1 + tol / 2))

    setup = Setup(
        symbol=symbol,
        timeframe=timeframe,
        as_of=pd.Timestamp(df["timestamp"].iloc[-1]).isoformat(),
        price=price,
        state="no_structure",
        tolerance=tol,
        at_level=at_level,
        supports=supports,
        resistances=resistances,
        levels=levels,
    )

    channel = fit_rising_channel(df, pivots, lookback, tol)
    if channel is None:
        # No setup to plan around; only report the next level to reclaim.
        setup.trigger = resistances[0] if resistances else None
        return setup

    _apply_structure(setup, df, channel, tol, above, last_closed=n - 1 if last_bar_complete else n - 2)
    return setup


def _apply_structure(setup: Setup, df: pd.DataFrame, channel: Channel, tol: float, above, last_closed: int):
    n = len(df)
    price = setup.price
    base_low = channel.anchor_price
    base_high = float(df["high"].iloc[channel.anchor_index : channel.structure_end + 1].max())
    ch_lo, ch_hi = channel.lower_at(n - 1), channel.upper_at(n - 1)
    setup.base_low, setup.base_high = base_low, base_high
    setup.channel_lower, setup.channel_upper = ch_lo, ch_hi
    setup.measured_move = base_high + (base_high - base_low)

    closes = df["close"]
    breakout_idx = next(
        (
            i
            for i in range(channel.structure_end + 1, last_closed + 1)
            if closes.iloc[i] > base_high * (1 + tol)
        ),
        None,
    )

    if breakout_idx is not None:
        setup.breakout_at = pd.Timestamp(df["timestamp"].iloc[breakout_idx]).isoformat()
        setup.measured_move_hit = bool(
            df["high"].iloc[breakout_idx:].max() >= setup.measured_move * (1 - tol)
        )
        z_lo, z_hi = sorted((base_high, ch_hi))
        if z_hi / z_lo < 1 + tol:
            z_lo, z_hi = z_lo * (1 - tol / 2), z_hi * (1 + tol / 2)
        setup.zone, setup.zone_kind = (z_lo, z_hi), "retest"
        setup.invalidation = z_lo * (1 - tol)

        if price < setup.invalidation:
            setup.state = "failed_breakout"
            setup.trigger = z_lo
            setup.targets = above(z_lo)[:2]
            setup.invalidation = None
            return
        setup.state = "retesting" if price <= z_hi * (1 + tol) else "extended"
        setup.trigger = setup.resistances[0] if setup.resistances else None
        setup.targets = above(setup.trigger)[:2] if setup.trigger else []
        if len(setup.targets) < 2 and not setup.measured_move_hit and setup.measured_move > price:
            setup.targets.append(setup.measured_move)
        return

    if price < base_low * (1 - tol):
        setup.state = "breakdown"
        setup.trigger = base_low
        setup.targets = above(base_low)[:2]
        return

    setup.state = "in_base"
    z_lo, z_hi = ch_lo * (1 - tol), ch_lo * (1 + tol)
    nearby = [p for p in setup.supports if ch_lo * (1 - 2 * tol) <= p <= ch_lo * (1 + 2 * tol)]
    if nearby:
        z_lo, z_hi = min(z_lo, *nearby), max(z_hi, *nearby)
    setup.zone, setup.zone_kind = (z_lo, z_hi), "sweep"
    setup.trigger = base_high
    setup.targets = above(base_high)[:2]
    if len(setup.targets) < 2:
        setup.targets.append(setup.measured_move)
    setup.invalidation = z_lo * (1 - tol)


def fmt_price(x: float | None) -> str:
    if x is None:
        return "-"
    if x >= 1000:
        return f"{x:,.0f}"
    if x >= 10:
        return f"{x:.2f}"
    if x >= 1:
        return f"{x:.3f}"
    return f"{x:.4f}"


def describe(setup: Setup) -> str:
    """Short plain-text summary, suitable for logs or a Telegram message."""
    f = fmt_price
    lines = [
        f"{setup.symbol} {setup.timeframe} | price {f(setup.price)} | {setup.state}",
        STATE_TEXT[setup.state],
    ]
    if setup.base_low is not None:
        mm = f"measured move {f(setup.measured_move)}"
        if setup.measured_move_hit is not None:
            mm += " (hit)" if setup.measured_move_hit else " (not hit)"
        lines.append(f"Base {f(setup.base_low)}-{f(setup.base_high)}, {mm}")
        lines.append(f"Channel now {f(setup.channel_lower)}-{f(setup.channel_upper)}")
    if setup.zone:
        lines.append(f"{setup.zone_kind.capitalize()} zone {f(setup.zone[0])}-{f(setup.zone[1])}")
    plan = [f"trigger {f(setup.trigger)}"]
    if setup.targets:
        plan.append("targets " + ", ".join(f(t) for t in setup.targets))
    plan.append(f"invalid below {f(setup.invalidation)}")
    lines.append(" | ".join(plan))
    if setup.at_level is not None:
        lines.append(f"Price is sitting on the {f(setup.at_level)} level.")
    return "\n".join(lines)
