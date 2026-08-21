import pandas as pd

from data.validate import timeframe_to_timedelta, validate_ohlcv


def _make_df(timestamps):
    n = len(timestamps)
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [1] * n,
            "high": [1] * n,
            "low": [1] * n,
            "close": [1] * n,
            "volume": [1] * n,
        }
    )


def test_dedup_removes_duplicate_rows():
    ts = list(pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC"))
    df = _make_df(ts + [ts[2]])
    clean, report = validate_ohlcv(df, "1h")
    assert report.duplicates_removed == 1
    assert len(clean) == 5


def test_gap_detection_counts_missing_bars():
    ts = list(pd.date_range("2024-01-01", periods=3, freq="h", tz="UTC"))
    ts += list(pd.date_range(ts[-1] + pd.Timedelta(hours=3), periods=2, freq="h", tz="UTC"))
    df = _make_df(ts)
    clean, report = validate_ohlcv(df, "1h")
    assert len(report.gaps) == 1
    assert report.gaps[0]["n_missing_bars"] == 2
    assert report.total_missing_bars == 2


def test_no_gaps_on_clean_series():
    ts = list(pd.date_range("2024-01-01", periods=10, freq="h", tz="UTC"))
    df = _make_df(ts)
    clean, report = validate_ohlcv(df, "1h")
    assert report.gaps == []
    assert report.is_monotonic


def test_sorts_into_monotonic_order():
    ts = list(pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC"))
    shuffled = [ts[2], ts[0], ts[4], ts[1], ts[3]]
    df = _make_df(shuffled)
    clean, report = validate_ohlcv(df, "1h")
    assert report.is_monotonic
    assert list(clean["timestamp"]) == ts


def test_timeframe_to_timedelta_units():
    assert timeframe_to_timedelta("15m") == pd.Timedelta(minutes=15)
    assert timeframe_to_timedelta("4h") == pd.Timedelta(hours=4)
    assert timeframe_to_timedelta("1d") == pd.Timedelta(days=1)
