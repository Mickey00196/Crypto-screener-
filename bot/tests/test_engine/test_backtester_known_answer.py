"""Hand-computed 5-trade known-answer test. Every fill price, fee, and P&L
below is computed by hand in this docstring and asserted to the cent.

12 bars (index 0-11), opens chosen so each transition's fill price is a
round number. Scripted signals (desired position after bar i's close,
executed at bar i+1's open):

    i:        0  1  2  3  4  5  6  7  8  9  10 11
    signal:   1  1  0  1  0  1  0  1  0  1  0  0

Execution trace (signal at i executes at open[i+1]):
    i=0 enter @ open[1]=102        i=9  enter @ open[10]=114
    i=2 exit  @ open[3]=105        i=10 exit  @ open[11]=118
    i=3 enter @ open[4]=104
    i=4 exit  @ open[5]=108
    i=5 enter @ open[6]=107
    i=6 exit  @ open[7]=111
    i=7 enter @ open[8]=110
    i=8 exit  @ open[9]=115

Size is fixed at 1 unit (FixedRiskManager), slippage_bps=0 (fills exactly at
open), fee_bps=10 (0.1%) applied to notional on both entry and exit, so
pnl = (exit - entry) * 1 - entry_price*0.001 - exit_price*0.001 :

    T1: entry=102 exit=105  price_pnl=3  fees=0.102+0.105=0.207  pnl=2.793
    T2: entry=104 exit=108  price_pnl=4  fees=0.104+0.108=0.212  pnl=3.788
    T3: entry=107 exit=111  price_pnl=4  fees=0.107+0.111=0.218  pnl=3.782
    T4: entry=110 exit=115  price_pnl=5  fees=0.110+0.115=0.225  pnl=4.775
    T5: entry=114 exit=118  price_pnl=4  fees=0.114+0.118=0.232  pnl=3.768

    total pnl = 2.793+3.788+3.782+4.775+3.768 = 18.906
"""

import pandas as pd
import pytest

from engine.backtester import Backtester
from engine.costs import CostModel
from tests.test_engine.strategy_fixtures import FixedRiskManager, ScriptedStrategy

OPENS = [100, 102, 101, 105, 104, 108, 107, 111, 110, 115, 114, 118]
SIGNALS = [1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0]

EXPECTED_TRADES = [
    (102, 105, 2.793),
    (104, 108, 3.788),
    (107, 111, 3.782),
    (110, 115, 4.775),
    (114, 118, 3.768),
]
EXPECTED_TOTAL_PNL = 18.906


def _make_df():
    timestamps = pd.date_range("2024-01-01", periods=len(OPENS), freq="h", tz="UTC")
    # open==high==low==close per bar so stop/take-profit (unused here, both None) never interfere
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": OPENS,
            "high": OPENS,
            "low": OPENS,
            "close": OPENS,
            "volume": [1.0] * len(OPENS),
        }
    )


def test_known_answer_five_trades_match_to_the_cent():
    df = _make_df()
    backtester = Backtester(
        cost_model=CostModel(taker_fee_bps=10.0, slippage_bps=0.0),
        risk_manager=FixedRiskManager(size=1.0),
        initial_capital=10_000.0,
    )
    result = backtester.run(df, ScriptedStrategy(SIGNALS), symbol="BTC/USDT")

    assert len(result.trades) == 5
    for trade, (entry, exit_, expected_pnl) in zip(result.trades, EXPECTED_TRADES, strict=True):
        assert trade.entry_price == pytest.approx(entry, abs=1e-9)
        assert trade.exit_price == pytest.approx(exit_, abs=1e-9)
        assert trade.pnl == pytest.approx(expected_pnl, abs=1e-9)

    assert sum(t.pnl for t in result.trades) == pytest.approx(EXPECTED_TOTAL_PNL, abs=1e-9)
    assert result.final_equity == pytest.approx(10_000.0 + EXPECTED_TOTAL_PNL, abs=1e-9)
    assert result.open_position is None
