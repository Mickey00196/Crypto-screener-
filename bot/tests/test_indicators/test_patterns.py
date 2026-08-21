import pandas as pd

from indicators.patterns import bearish_engulfing, bullish_engulfing, doji, hammer, inside_bar, shooting_star


def test_doji_detected_for_tiny_body():
    df = pd.DataFrame({"open": [100.0], "close": [100.4], "high": [105.0], "low": [95.0]})
    assert bool(doji(df, body_threshold=0.1).iloc[0])


def test_doji_not_detected_for_large_body():
    df = pd.DataFrame({"open": [100.0], "close": [110.0], "high": [112.0], "low": [99.0]})
    assert not bool(doji(df, body_threshold=0.1).iloc[0])


def test_inside_bar_detected():
    df = pd.DataFrame({"high": [110.0, 108.0], "low": [90.0, 95.0]})
    assert bool(inside_bar(df).iloc[1])


def test_inside_bar_not_detected_when_range_expands():
    df = pd.DataFrame({"high": [110.0, 115.0], "low": [90.0, 85.0]})
    assert not bool(inside_bar(df).iloc[1])


def test_bullish_engulfing_detected():
    df = pd.DataFrame(
        {
            "open": [10.0, 8.5],
            "close": [9.0, 11.0],
            "high": [10.2, 11.2],
            "low": [8.8, 8.3],
        }
    )
    assert bool(bullish_engulfing(df).iloc[1])


def test_bearish_engulfing_detected():
    df = pd.DataFrame(
        {
            "open": [9.0, 11.0],
            "close": [10.0, 8.5],
            "high": [10.2, 11.2],
            "low": [8.8, 8.3],
        }
    )
    assert bool(bearish_engulfing(df).iloc[1])


def test_hammer_detected():
    df = pd.DataFrame({"open": [10.0], "close": [10.2], "high": [10.3], "low": [8.0]})
    assert bool(hammer(df).iloc[0])


def test_shooting_star_detected():
    df = pd.DataFrame({"open": [10.0], "close": [9.8], "high": [12.0], "low": [9.7]})
    assert bool(shooting_star(df).iloc[0])
