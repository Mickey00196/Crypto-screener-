import pandas as pd
import pytest

from engine.costs import CostModel
from engine.types import SizeDecision
from live.state import load_state
from live.trading_loop import TradingLoop


class ScriptedSignalStrategy:
    """Returns a fixed direction regardless of input, purely for testing the
    loop's plumbing (open/close routing, idempotency, state persistence)."""

    def __init__(self, direction: int):
        self.params = {"direction": direction}

    def generate_signals(self, df):
        return pd.Series([self.params["direction"]] * len(df), index=df.index)


class FixedDecisionRiskManager:
    def __init__(self, size=0.1, stop_price=None, take_profit_price=None):
        self.size = size
        self.stop_price = stop_price
        self.take_profit_price = take_profit_price

    def decide(self, side, symbol, df_so_far, equity, open_positions):
        return SizeDecision(
            size=self.size, stop_price=self.stop_price, take_profit_price=self.take_profit_price
        )

    def should_halt(self, equity_history, initial_capital):
        return False


def _df(n=10, start_price=100.0):
    ts = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    prices = [start_price + i for i in range(n)]
    return pd.DataFrame(
        {"timestamp": ts, "open": prices, "high": prices, "low": prices, "close": prices, "volume": [1.0] * n}
    )


def _loop(strategy, risk_manager, state_path, trading_mode="paper"):
    return TradingLoop(
        strategy=strategy,
        risk_manager=risk_manager,
        symbol="BTC/EUR",
        timeframe="1h",
        cost_model=CostModel(taker_fee_bps=10.0, slippage_bps=5.0),
        state_path=state_path,
        trading_mode=trading_mode,
    )


def test_opens_a_position_when_signal_goes_long(tmp_path):
    loop = _loop(ScriptedSignalStrategy(1), FixedDecisionRiskManager(size=0.1), tmp_path / "state.json")
    loop.process_latest_closed_bar(_df())
    assert "BTC/EUR" in loop.state.positions
    assert loop.state.positions["BTC/EUR"].side == "long"


def test_flat_signal_does_not_open_a_position(tmp_path):
    loop = _loop(ScriptedSignalStrategy(0), FixedDecisionRiskManager(size=0.1), tmp_path / "state.json")
    loop.process_latest_closed_bar(_df())
    assert loop.state.positions == {}


def test_reprocessing_same_bar_is_a_noop(tmp_path):
    """Idempotency: after a restart, re-seeing the same latest-closed bar
    must not open a second position or duplicate trade log entries."""
    state_path = tmp_path / "state.json"
    loop = _loop(ScriptedSignalStrategy(1), FixedDecisionRiskManager(size=0.1), state_path)
    df = _df()
    loop.process_latest_closed_bar(df)
    positions_after_first = dict(loop.state.positions)

    # simulate a restart: fresh TradingLoop instance loading persisted state
    loop2 = _loop(ScriptedSignalStrategy(1), FixedDecisionRiskManager(size=0.1), state_path)
    loop2.process_latest_closed_bar(df)  # same df, same latest closed bar

    assert loop2.state.positions.keys() == positions_after_first.keys()
    assert len(loop2.state.trade_log) == 0  # no spurious close+reopen


def test_opposite_signal_closes_then_reopens(tmp_path):
    state_path = tmp_path / "state.json"
    loop = _loop(ScriptedSignalStrategy(1), FixedDecisionRiskManager(size=0.1), state_path)
    loop.process_latest_closed_bar(_df(n=10))
    assert loop.state.positions["BTC/EUR"].side == "long"

    loop2 = _loop(ScriptedSignalStrategy(-1), FixedDecisionRiskManager(size=0.1), state_path)
    loop2.process_latest_closed_bar(_df(n=11))  # one more bar -> new latest closed bar
    assert loop2.state.positions["BTC/EUR"].side == "short"
    assert len(loop2.state.trade_log) == 1  # the long was closed


def test_live_mode_without_credentials_raises_on_construction_attempt(tmp_path, monkeypatch):
    monkeypatch.delenv("BITVAVO_API_KEY", raising=False)
    monkeypatch.delenv("BITVAVO_API_SECRET", raising=False)
    loop = _loop(
        ScriptedSignalStrategy(1),
        FixedDecisionRiskManager(size=0.1),
        tmp_path / "state.json",
        trading_mode="live",
    )
    # constructing the loop is fine (LiveBroker.from_env builds an exchange
    # client), but actually routing an order without credentials must raise
    from live.live_broker import LiveTradingDisabledError

    with pytest.raises(LiveTradingDisabledError):
        loop.process_latest_closed_bar(_df())


def test_seconds_until_next_bar_close_hand_computed():
    from datetime import UTC, datetime

    loop = TradingLoop(
        strategy=ScriptedSignalStrategy(0),
        risk_manager=FixedDecisionRiskManager(),
        symbol="BTC/EUR",
        timeframe="1h",
        cost_model=CostModel(taker_fee_bps=1.0, slippage_bps=1.0),
        state_path="/tmp/unused_state.json",
    )
    now = datetime(2024, 1, 1, 10, 15, 0, tzinfo=UTC)  # 15 minutes past the hour
    seconds = loop.seconds_until_next_bar_close(now)
    assert seconds == pytest.approx(45 * 60, abs=1)


def test_state_persists_across_process_calls_via_disk(tmp_path):
    state_path = tmp_path / "state.json"
    loop = _loop(ScriptedSignalStrategy(1), FixedDecisionRiskManager(size=0.1), state_path)
    loop.process_latest_closed_bar(_df())
    assert state_path.exists()

    reloaded = load_state(state_path)
    assert "BTC/EUR" in reloaded.positions
