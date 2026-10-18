import math

import pytest

from setups.channel import fit_rising_channel
from setups.levels import find_pivots
from tests.test_setups.series import aero_like, downtrend, range_bound


def test_aero_channel_anchors_on_base_low_with_shallowest_slope():
    df = aero_like()
    ch = fit_rising_channel(df, find_pivots(df), lookback=52, tolerance=0.05)

    assert ch is not None
    assert (ch.anchor_index, ch.structure_end) == (30, 54)
    assert ch.anchor_price == pytest.approx(0.29)
    # shallowest of 0.29->0.32 (15 bars) and 0.29->0.40 (24 bars) is the June low
    assert ch.slope == pytest.approx(math.log(0.32 / 0.29) / 15)
    assert ch.lower_at(45) == pytest.approx(0.32)


def test_no_later_swing_low_sits_below_the_lower_line():
    df = aero_like()
    pivots = find_pivots(df)
    ch = fit_rising_channel(df, pivots)

    for p in pivots:
        if p.kind == "low" and not p.provisional and p.index >= ch.anchor_index:
            assert p.price >= ch.lower_at(p.index) * (1 - 1e-9)


def test_upper_line_runs_through_highest_high_of_the_structure():
    df = aero_like()
    ch = fit_rising_channel(df, find_pivots(df))

    window = range(ch.anchor_index, ch.structure_end + 1)
    assert max(df["high"].iloc[i] / ch.upper_at(i) for i in window) == pytest.approx(1.0)
    assert ch.upper_at(49) == pytest.approx(0.60)  # the July 2026 high defines the top


def test_range_channel_and_touch_count():
    df = range_bound()
    ch = fit_rising_channel(df, find_pivots(df), tolerance=0.03)

    assert ch is not None and ch.touches == 3  # all three rising lows sit on the line


def test_downtrend_has_no_rising_channel():
    df = downtrend()
    assert fit_rising_channel(df, find_pivots(df)) is None


def test_lookback_excludes_older_lows():
    df = aero_like()
    ch = fit_rising_channel(df, find_pivots(df), lookback=20)  # only lows from idx 44 on

    assert ch is not None and ch.anchor_index == 45
