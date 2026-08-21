import pandas as pd
import pytest

from indicators.volume import cmf, mfi, obv, vwap


def test_obv_hand_computed():
    df = pd.DataFrame(
        {
            "close": [10.0, 11.0, 10.5, 12.0],
            "volume": [100.0, 200.0, 150.0, 300.0],
        }
    )
    result = obv(df)
    # bar0: no prior close -> diff NaN -> sign 0 -> obv=0
    # bar1: close up -> +200 -> obv=200
    # bar2: close down -> -150 -> obv=50
    # bar3: close up -> +300 -> obv=350
    assert result.iloc[0] == pytest.approx(0.0)
    assert result.iloc[1] == pytest.approx(200.0)
    assert result.iloc[2] == pytest.approx(50.0)
    assert result.iloc[3] == pytest.approx(350.0)


def test_vwap_hand_computed():
    df = pd.DataFrame(
        {
            "high": [11.0, 12.0],
            "low": [9.0, 10.0],
            "close": [10.0, 11.0],
            "volume": [100.0, 200.0],
        }
    )
    result = vwap(df)
    tp0 = (11 + 9 + 10) / 3  # 10.0
    tp1 = (12 + 10 + 11) / 3  # 11.0
    expected_vwap1 = (tp0 * 100 + tp1 * 200) / (100 + 200)
    assert result.iloc[0] == pytest.approx(tp0)
    assert result.iloc[1] == pytest.approx(expected_vwap1)


def test_mfi_bounded_0_100():
    import numpy as np

    rng = np.random.default_rng(5)
    n = 60
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, n)))
    df = pd.DataFrame(
        {
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": rng.uniform(100, 200, n),
        }
    )
    result = mfi(df, period=14).dropna()
    assert (result >= 0).all()
    assert (result <= 100).all()


def test_cmf_sign_matches_close_position_in_range():
    # close at the high of the range every bar -> CMF should be strongly positive
    df = pd.DataFrame(
        {
            "high": [12.0] * 10,
            "low": [10.0] * 10,
            "close": [12.0] * 10,
            "volume": [100.0] * 10,
        }
    )
    result = cmf(df, period=5)
    assert result.iloc[-1] == pytest.approx(1.0)
