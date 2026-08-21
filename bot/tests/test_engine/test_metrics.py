import pandas as pd
import pytest

from engine import metrics
from engine.types import Side, Trade

TS = pd.Timestamp("2024-01-01", tz="UTC")


def _trade(pnl, risk_per_unit=None, size=1.0):
    return Trade(
        symbol="BTC/USDT",
        side=Side.LONG,
        entry_time=TS,
        entry_price=100.0,
        exit_time=TS,
        exit_price=100.0 + pnl,
        size=size,
        fees_paid=0.0,
        pnl=pnl,
        exit_reason="signal",
        risk_per_unit=risk_per_unit,
    )


def test_win_rate():
    trades = [_trade(5), _trade(-2), _trade(3), _trade(-1)]
    assert metrics.win_rate(trades) == 0.5


def test_win_rate_empty():
    assert metrics.win_rate([]) == 0.0


def test_profit_factor():
    trades = [_trade(10), _trade(-5), _trade(5)]
    assert metrics.profit_factor(trades) == pytest.approx(15 / 5)


def test_expectancy():
    trades = [_trade(10), _trade(-4)]
    assert metrics.expectancy(trades) == pytest.approx(3.0)


def test_avg_r_multiple():
    trades = [_trade(10, risk_per_unit=5.0), _trade(-5, risk_per_unit=5.0)]
    # R = pnl / (risk_per_unit * size): 10/5=2, -5/5=-1 => avg 0.5
    assert metrics.avg_r_multiple(trades) == pytest.approx(0.5)


def test_max_drawdown():
    eq = pd.Series([100, 110, 90, 95, 120])
    dd = metrics.max_drawdown(eq)
    assert dd == pytest.approx((90 - 110) / 110)


def test_max_drawdown_empty_series():
    assert metrics.max_drawdown(pd.Series(dtype=float)) == 0.0


def test_trade_count():
    assert metrics.trade_count([_trade(1), _trade(2)]) == 2
