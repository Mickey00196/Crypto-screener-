import json

import pytest

from setups.scenario import analyze, describe, fmt_price
from tests.test_setups.series import aero_like, build_series, downtrend, range_bound


def test_aero_reproduces_the_hand_drawn_setup():
    s = analyze(aero_like(), symbol="AERO/USD")

    assert s.state == "extended"
    assert s.price == pytest.approx(0.79)
    assert (s.base_low, s.base_high) == pytest.approx((0.29, 0.60))
    assert s.measured_move == pytest.approx(0.91)
    assert s.measured_move_hit is True
    assert s.zone == pytest.approx((0.60, 0.658), rel=0.01)
    assert s.trigger == pytest.approx(1.00)
    assert s.targets == pytest.approx([1.30, 1.58])
    assert 0.54 < s.invalidation < 0.59
    assert s.channel_lower == pytest.approx(0.36, rel=0.02)
    assert s.supports[0] == pytest.approx(0.75)


def test_pullback_into_zone_is_a_retest():
    s = analyze(aero_like(last_close=0.63))

    assert s.state == "retesting"
    assert s.zone[0] <= s.price <= s.zone[1]
    assert s.trigger > s.price


def test_close_back_inside_the_base_is_a_failed_breakout():
    s = analyze(aero_like(last_close=0.50))

    assert s.state == "failed_breakout"
    assert s.trigger == pytest.approx(s.zone[0])  # reclaim the zone first
    assert s.invalidation is None


def test_forming_candle_cannot_confirm_a_breakout():
    # same range, but only the last (forming) candle closes above the base top
    df = build_series({0: 76, 10: 70, 17: 88, 25: 74, 33: 90, 40: 78, 47: 93, 51: 88, 52: 100})

    assert analyze(df).state == "in_base"
    confirmed = analyze(df, last_bar_complete=True)
    assert confirmed.breakout_at is not None
    assert confirmed.state in {"retesting", "extended"}


def test_range_with_rising_lows_is_in_base_with_sweep_zone_below_price():
    s = analyze(range_bound(), symbol="BTC/USD")

    assert s.state == "in_base"
    assert s.zone_kind == "sweep"
    assert s.zone[1] < s.price
    assert s.trigger == pytest.approx(s.base_high)
    assert len(s.targets) == 2 and all(t > s.trigger for t in s.targets)
    assert s.invalidation < s.zone[0]


def test_below_base_low_is_a_breakdown():
    s = analyze(range_bound(last_close=60.0))

    assert s.state == "breakdown"
    assert s.trigger == pytest.approx(s.base_low)


def test_downtrend_has_no_structure():
    s = analyze(downtrend())

    assert s.state == "no_structure"
    assert s.zone is None and s.targets == [] and s.invalidation is None


def test_to_dict_is_json_serializable():
    payload = analyze(aero_like(), symbol="AERO/USD").to_dict()
    restored = json.loads(json.dumps(payload))

    assert restored["state"] == "extended"
    assert len(restored["levels"]) == len(payload["levels"])


def test_describe_mentions_plan():
    text = describe(analyze(aero_like(), symbol="AERO/USD"))

    assert "AERO/USD 1w" in text and "extended" in text
    assert "trigger 1.000" in text and "targets 1.300, 1.580" in text


def test_too_few_candles_raises():
    with pytest.raises(ValueError):
        analyze(aero_like().head(5))


@pytest.mark.parametrize(
    ("x", "out"), [(81550.3, "81,550"), (12.345, "12.35"), (1.5, "1.500"), (0.79184, "0.7918")]
)
def test_fmt_price(x, out):
    assert fmt_price(x) == out
