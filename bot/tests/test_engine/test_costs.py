import pytest

from engine.costs import CostModel
from engine.types import Side


def test_entry_slippage_is_adverse_for_both_sides():
    cost = CostModel(taker_fee_bps=0.0, slippage_bps=10.0)  # 0.1%
    long_fill = cost.entry_fill_price(100.0, Side.LONG)
    short_fill = cost.entry_fill_price(100.0, Side.SHORT)
    assert long_fill == pytest.approx(100.1)  # buying costs more
    assert short_fill == pytest.approx(99.9)  # selling short receives less


def test_exit_slippage_is_adverse_for_both_sides():
    cost = CostModel(taker_fee_bps=0.0, slippage_bps=10.0)
    long_exit = cost.exit_fill_price(100.0, Side.LONG)
    short_exit = cost.exit_fill_price(100.0, Side.SHORT)
    assert long_exit == pytest.approx(99.9)  # selling to close a long receives less
    assert short_exit == pytest.approx(100.1)  # buying to close a short costs more


def test_zero_slippage_returns_reference_price():
    cost = CostModel(taker_fee_bps=0.0, slippage_bps=0.0)
    assert cost.entry_fill_price(100.0, Side.LONG) == 100.0
    assert cost.exit_fill_price(100.0, Side.SHORT) == 100.0


def test_fee_is_bps_of_notional():
    cost = CostModel(taker_fee_bps=25.0, slippage_bps=0.0)  # 0.25%
    assert cost.fee(1000.0) == pytest.approx(2.5)


def test_funding_cost_scales_with_periods():
    cost = CostModel(taker_fee_bps=0.0, slippage_bps=0.0, funding_bps_per_8h=1.0)
    assert cost.funding_cost(10_000.0, n_8h_periods=3) == pytest.approx(3.0)
