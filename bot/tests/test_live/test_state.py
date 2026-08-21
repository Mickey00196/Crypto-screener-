from live.state import OpenPositionState, TradingState, load_state, save_state


def test_load_state_returns_fresh_state_when_file_missing(tmp_path):
    state = load_state(tmp_path / "state.json", default_initial_capital=5000.0, trading_mode="paper")
    assert state.cash == 5000.0
    assert state.initial_capital == 5000.0
    assert state.positions == {}
    assert state.trade_log == []


def test_save_and_load_roundtrip_preserves_positions_and_log(tmp_path):
    path = tmp_path / "state.json"
    state = TradingState(trading_mode="paper", cash=9500.0, initial_capital=10_000.0)
    state.positions["BTC/EUR"] = OpenPositionState(
        symbol="BTC/EUR", side="long", size=0.1, entry_price=40000.0, entry_time="2024-01-01T00:00:00Z"
    )
    state.trade_log.append({"symbol": "ETH/EUR", "pnl": 12.5})
    state.last_processed_bar_time["BTC/EUR"] = "2024-01-01T01:00:00Z"

    save_state(state, path)
    loaded = load_state(path)

    assert loaded.cash == 9500.0
    assert loaded.initial_capital == 10_000.0
    assert loaded.positions["BTC/EUR"].entry_price == 40000.0
    assert loaded.trade_log == [{"symbol": "ETH/EUR", "pnl": 12.5}]
    assert loaded.last_processed_bar_time["BTC/EUR"] == "2024-01-01T01:00:00Z"


def test_save_state_is_atomic_no_leftover_tmp_file(tmp_path):
    path = tmp_path / "state.json"
    save_state(TradingState(trading_mode="paper", cash=100.0, initial_capital=100.0), path)
    assert path.exists()
    assert not path.with_suffix(".json.tmp").exists()
