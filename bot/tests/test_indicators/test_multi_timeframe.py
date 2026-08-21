import pandas as pd
import pytest

from indicators.multi_timeframe import align_higher_timeframe, resample_ohlcv


def test_resample_ohlcv_aggregates_correctly():
    ts = pd.date_range("2024-01-01", periods=8, freq="h", tz="UTC")
    df = pd.DataFrame(
        {
            "timestamp": ts,
            "open": [1, 2, 3, 4, 5, 6, 7, 8],
            "high": [10, 20, 30, 40, 50, 60, 70, 80],
            "low": [1, 2, 3, 4, 5, 6, 7, 8],
            "close": [2, 3, 4, 5, 6, 7, 8, 9],
            "volume": [1] * 8,
        }
    )
    result = resample_ohlcv(df, "4h")
    assert len(result) == 2
    first = result.iloc[0]
    assert first["open"] == 1
    assert first["high"] == 40
    assert first["low"] == 1
    assert first["close"] == 5
    assert first["volume"] == 4
    assert first["timestamp"] == ts[0]
    assert first["available_at"] == ts[0] + pd.Timedelta(hours=4)


def test_resample_rejects_unsupported_timeframe():
    df = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp.now(tz="UTC")],
            "open": [1],
            "high": [1],
            "low": [1],
            "close": [1],
            "volume": [1],
        }
    )
    with pytest.raises(ValueError):
        resample_ohlcv(df, "3h")


def test_align_higher_timeframe_never_leaks_still_forming_bar():
    """The core anti-leak requirement: the 4h bar spanning hours 0-3 is only
    visible starting at hour 4 (its close time) — never during hours 0-3
    while it's still forming."""
    ts = pd.date_range("2024-01-01", periods=8, freq="h", tz="UTC")
    base = pd.DataFrame(
        {
            "timestamp": ts,
            "open": [0] * 8,
            "high": [0] * 8,
            "low": [0] * 8,
            "close": [0] * 8,
            "volume": [0] * 8,
        }
    )
    source = pd.DataFrame(
        {
            "timestamp": ts,
            "open": [1, 2, 3, 4, 5, 6, 7, 8],
            "high": [10, 20, 30, 40, 50, 60, 70, 80],
            "low": [1] * 8,
            "close": [1, 2, 3, 4, 5, 6, 7, 8],
            "volume": [1] * 8,
        }
    )
    htf = resample_ohlcv(source, "4h")
    aligned = align_higher_timeframe(base, htf)

    for i in range(4):
        assert pd.isna(aligned.loc[i, "close_htf"]), f"hour {i}: forming 4h bar leaked"
    for i in range(4, 8):
        assert aligned.loc[i, "close_htf"] == 4  # first 4h bar's close (hour3's close value)
