import pandas as pd
import pytest

from engine.types import Position, Side
from risk.risk_manager import RiskConfig, RiskManager


def _constant_tr_df(n=20, low=99.0, atr_period=5):
    """Bars with constant true range = 2.0 (high=low+2, close midpoint,
    prev_close chosen so gap terms never dominate) so ATR converges to
    exactly 2.0 after Wilder warmup — see indicators/trend.py's own ATR
    hand-computed test for the underlying formula proof."""
    ts = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    highs = [low + 2] * n
    lows = [low] * n
    closes = [low + 1] * n
    return pd.DataFrame({"timestamp": ts, "high": highs, "low": lows, "close": closes})


def _config(**overrides):
    defaults = dict(
        max_risk_per_trade_pct=1.0,
        max_position_pct=20.0,
        max_concurrent_positions=3,
        daily_loss_limit_pct=3.0,
        max_drawdown_kill_switch_pct=15.0,
        atr_period=5,
        atr_stop_multiplier=2.0,
        atr_target_multiplier=3.0,
    )
    defaults.update(overrides)
    return RiskConfig(**defaults)


def test_decide_sizes_by_risk_when_below_position_cap():
    # atr=2.0 -> stop_distance=4.0, risk_amount=10000*1%=100 -> size_by_risk=25
    # max_notional=10000*20%=2000, reference_price=100 -> size_by_cap=20 (binding)
    df = _constant_tr_df(atr_period=5)
    rm = RiskManager(_config(max_position_pct=1000.0))  # cap far above risk-based size
    decision = rm.decide(Side.LONG, "BTC/USDT", df, equity=10_000.0, open_positions={})
    assert decision.size == pytest.approx(25.0, rel=1e-6)
    assert decision.stop_price == pytest.approx(100.0 - 4.0)
    assert decision.take_profit_price == pytest.approx(100.0 + 6.0)  # atr*target_mult=2*3=6


def test_decide_caps_size_at_max_position_pct():
    df = _constant_tr_df(atr_period=5)
    rm = RiskManager(_config(max_position_pct=20.0))
    decision = rm.decide(Side.LONG, "BTC/USDT", df, equity=10_000.0, open_positions={})
    assert decision.size == pytest.approx(20.0, rel=1e-6)  # capped below the 25.0 risk-based size


def test_decide_short_side_stop_and_target_directions():
    df = _constant_tr_df(atr_period=5)
    rm = RiskManager(_config(max_position_pct=1000.0))
    decision = rm.decide(Side.SHORT, "BTC/USDT", df, equity=10_000.0, open_positions={})
    assert decision.stop_price == pytest.approx(100.0 + 4.0)
    assert decision.take_profit_price == pytest.approx(100.0 - 6.0)


def test_decide_refuses_when_max_concurrent_positions_reached():
    df = _constant_tr_df(atr_period=5)
    rm = RiskManager(_config(max_concurrent_positions=1))
    existing = {
        "ETH/USDT": Position(
            symbol="ETH/USDT",
            side=Side.LONG,
            size=1.0,
            entry_price=100.0,
            entry_time=df["timestamp"].iloc[0],
            entry_fee=0.0,
        )
    }
    decision = rm.decide(Side.LONG, "BTC/USDT", df, equity=10_000.0, open_positions=existing)
    assert decision.size == 0


def test_decide_refuses_when_insufficient_history_for_atr():
    df = _constant_tr_df(n=3, atr_period=5)
    rm = RiskManager(_config())
    decision = rm.decide(Side.LONG, "BTC/USDT", df, equity=10_000.0, open_positions={})
    assert decision.size == 0


def test_daily_loss_limit_blocks_new_positions_same_day():
    df = _constant_tr_df(atr_period=5)
    rm = RiskManager(_config(daily_loss_limit_pct=3.0))
    # first call of the day establishes day_start_equity=10000
    rm.decide(Side.LONG, "BTC/USDT", df, equity=10_000.0, open_positions={})
    # equity has since dropped 5% intraday -> daily loss limit (3%) breached
    decision = rm.decide(Side.LONG, "BTC/USDT", df, equity=9_500.0, open_positions={})
    assert decision.size == 0


def test_daily_loss_limit_resets_on_new_day():
    df_day1 = _constant_tr_df(atr_period=5)
    df_day2 = df_day1.copy()
    df_day2["timestamp"] = df_day2["timestamp"] + pd.Timedelta(days=2)

    rm = RiskManager(_config(daily_loss_limit_pct=3.0, max_position_pct=1000.0))
    rm.decide(Side.LONG, "BTC/USDT", df_day1, equity=10_000.0, open_positions={})
    breached = rm.decide(Side.LONG, "BTC/USDT", df_day1, equity=9_500.0, open_positions={})
    assert breached.size == 0

    # new day -> daily tracking resets, even though equity is still "down" vs day1's start
    recovered = rm.decide(Side.LONG, "BTC/USDT", df_day2, equity=9_500.0, open_positions={})
    assert recovered.size > 0


def test_should_halt_triggers_at_drawdown_threshold():
    rm = RiskManager(_config(max_drawdown_kill_switch_pct=15.0))
    # peak 10000, current 8400 -> 16% drawdown, breaches 15%
    assert rm.should_halt([9000, 10_000, 9500, 8400], initial_capital=10_000.0) is True


def test_should_halt_false_below_threshold():
    rm = RiskManager(_config(max_drawdown_kill_switch_pct=15.0))
    # peak 10000, current 9000 -> 10% drawdown, below 15%
    assert rm.should_halt([9000, 10_000, 9500, 9000], initial_capital=10_000.0) is False


def test_should_halt_false_on_empty_history():
    rm = RiskManager(_config())
    assert rm.should_halt([], initial_capital=10_000.0) is False
