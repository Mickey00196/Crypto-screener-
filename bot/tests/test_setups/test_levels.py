import pandas as pd
import pytest

from setups.levels import Pivot, auto_tolerance, build_levels, cluster_pivots, find_pivots, round_levels
from tests.test_setups.series import aero_like, build_series


@pytest.mark.parametrize(
    ("price", "expected"),
    [
        (0.79, (0.5, 1.0)),
        (81_550, (50_000, 100_000)),
        (4_000, (2_000, 5_000)),
        (180, (100, 200)),
        (1.0, (1.0, 2.0)),
    ],
)
def test_round_levels_use_the_1_2_5_series(price, expected):
    assert round_levels(price) == pytest.approx(expected)


def test_round_levels_rejects_non_positive_price():
    with pytest.raises(ValueError):
        round_levels(0)


def test_confirmed_pivots_on_aero_series():
    pivots = find_pivots(aero_like(), k=3)
    confirmed = {(p.index, round(p.price, 2), p.kind) for p in pivots if not p.provisional}

    assert confirmed == {
        (4, 1.58, "high"),
        (11, 0.75, "low"),
        (14, 1.30, "high"),
        (30, 0.29, "low"),
        (41, 0.55, "high"),
        (45, 0.32, "low"),
        (49, 0.60, "high"),
        (54, 0.40, "low"),
    }


def test_fresh_swing_high_is_added_as_provisional_pivot():
    # AERO's 1.00 high is 1 candle old: too recent to confirm with k=3
    provisional = [p for p in find_pivots(aero_like(), k=3) if p.provisional]

    assert [(p.index, round(p.price, 2), p.kind) for p in provisional] == [(62, 1.0, "high")]


def test_forming_candle_is_never_a_pivot():
    df = build_series({0: 10, 20: 20, 21: 30})  # last (forming) candle makes the highest high
    pivots = find_pivots(df, k=3)

    assert all(p.index < len(df) - 1 for p in pivots)


def test_clustering_merges_nearby_pivots_and_counts_touches():
    ts = pd.Timestamp("2026-01-05", tz="UTC")
    pivots = [Pivot(10, ts, 100.0, "high"), Pivot(20, ts, 102.0, "low"), Pivot(30, ts, 120.0, "high")]

    levels = cluster_pivots(pivots, tolerance=0.03, now_index=30)

    assert [(lv.touches, lv.kinds) for lv in levels] == [(2, ("high", "low")), (1, ("high",))]
    assert levels[0].price == pytest.approx(101.0)


def test_recent_touches_score_higher():
    ts = pd.Timestamp("2026-01-05", tz="UTC")
    old, new = Pivot(0, ts, 50.0, "low"), Pivot(100, ts, 80.0, "low")

    old_level, new_level = cluster_pivots([old, new], tolerance=0.03, now_index=100)

    assert new_level.score > old_level.score


def test_build_levels_keeps_trigger_and_targets_above_price():
    df = aero_like()
    levels = build_levels(df, find_pivots(df), tolerance=auto_tolerance(df), max_levels=3)
    above = [round(lv.price, 2) for lv in levels if lv.price > df["close"].iloc[-1]]

    # even with max_levels=3, the nearest three levels above price survive
    assert above[:3] == [1.0, 1.3, 1.58]


def test_round_number_merges_into_matching_level():
    df = aero_like()
    levels = build_levels(df, find_pivots(df), tolerance=auto_tolerance(df))
    one = next(lv for lv in levels if abs(lv.price - 1.0) < 0.01)

    assert one.is_round and one.touches == 1


def test_auto_tolerance_is_clamped():
    df = aero_like()
    assert 0.02 <= auto_tolerance(df) <= 0.08
