import pandas as pd
import pytest

from indicators.momentum import cci, roc, rsi, stoch_rsi, stochastic, williams_r


def test_rsi_hand_computed_wilder():
    """closes = [10, 12, 11, 13, 15, 14, 16], period=3.
    diffs:      [-, 2, -1, 2, 2, -1, 2]
    gains:      [-, 2, 0, 2, 2, 0, 2]
    losses:     [-, 0, 1, 0, 0, 1, 0]
    Wilder seed at index3 (mean of gains[1:4], losses[1:4]):
        avg_gain[3] = mean(2,0,2) = 4/3, avg_loss[3] = mean(0,1,0) = 1/3
        rs[3] = 4  ->  RSI[3] = 100 - 100/5 = 80.0
    Recursion out[i] = (out[i-1]*(period-1) + values[i]) / period, to index6:
        avg_gain[4] = (4/3*2 + 2)/3 = 14/9
        avg_gain[5] = (14/9*2 + 0)/3 = 28/27
        avg_gain[6] = (28/27*2 + 2)/3 = 110/81
        avg_loss[4] = (1/3*2 + 0)/3 = 2/9
        avg_loss[5] = (2/9*2 + 1)/3 = 13/27
        avg_loss[6] = (13/27*2 + 0)/3 = 26/81
        rs[6] = (110/81)/(26/81) = 55/13
        RSI[6] = 100 - 100/(1 + 55/13) = 100 - 1300/68 = 80.88235294117646
    """
    closes = pd.Series([10.0, 12.0, 11.0, 13.0, 15.0, 14.0, 16.0])
    result = rsi(closes, period=3)
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[2])
    assert result.iloc[3] == pytest.approx(80.0, abs=1e-9)
    assert result.iloc[6] == pytest.approx(80.88235294117646, abs=1e-9)


def test_rsi_bounded_0_100():
    import numpy as np

    rng = np.random.default_rng(0)
    closes = pd.Series(100 + np.cumsum(rng.normal(0, 1, 200)))
    result = rsi(closes, period=14).dropna()
    assert (result >= 0).all()
    assert (result <= 100).all()


def test_stochastic_hand_computed():
    df = pd.DataFrame(
        {
            "high": [10, 12, 14, 13, 15],
            "low": [8, 9, 10, 11, 12],
            "close": [9, 11, 13, 12, 14],
        }
    )
    result = stochastic(df, k_period=3, d_period=2)
    # window idx0-2: low_min=8, high_max=14, close=13 -> %K = 100*(13-8)/(14-8)=83.3333
    assert result["percent_k"].iloc[2] == pytest.approx(100 * (13 - 8) / (14 - 8))


def test_williams_r_hand_computed():
    df = pd.DataFrame(
        {
            "high": [10, 12, 14],
            "low": [8, 9, 10],
            "close": [9, 11, 13],
        }
    )
    result = williams_r(df, period=3)
    # high_max=14, low_min=8, close=13 -> -100*(14-13)/(14-8) = -16.6667
    assert result.iloc[2] == pytest.approx(-100 * (14 - 13) / (14 - 8))


def test_roc_hand_computed():
    closes = pd.Series([100.0, 105.0, 110.0, 121.0])
    result = roc(closes, period=3)
    # (121-100)/100 * 100 = 21.0
    assert result.iloc[3] == pytest.approx(21.0)


def test_cci_zero_when_typical_price_equals_sma():
    df = pd.DataFrame({"high": [10] * 5, "low": [10] * 5, "close": [10] * 5})
    result = cci(df, period=3)
    # constant series -> typical price == its own SMA -> CCI numerator is 0
    assert result.iloc[-1] == pytest.approx(0.0) or pd.isna(result.iloc[-1])


def test_stoch_rsi_bounded_0_100():
    import numpy as np

    rng = np.random.default_rng(2)
    closes = pd.Series(100 + np.cumsum(rng.normal(0, 1, 200)))
    result = stoch_rsi(closes, period=14, k_period=3, d_period=3)["stoch_rsi"].dropna()
    assert (result >= -1e-9).all()
    assert (result <= 100 + 1e-9).all()
