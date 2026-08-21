"""Headless Streamlit smoke test (streamlit.testing.v1.AppTest) — proves
dashboard/app.py actually renders without error against a real state file,
not just that its pure helper functions work in isolation."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from live.state import OpenPositionState, TradingState, save_state

APP_PATH = str(Path(__file__).resolve().parent.parent.parent / "dashboard" / "app.py")


@pytest.fixture
def state_path(tmp_path):
    path = tmp_path / "paper_state.json"
    state = TradingState(trading_mode="paper", cash=10_050.0, initial_capital=10_000.0)
    state.trade_log = [
        {
            "symbol": "BTC/EUR",
            "side": "long",
            "entry_time": "2024-01-01T00:00:00Z",
            "entry_price": 40000.0,
            "exit_time": "2024-01-01T01:00:00Z",
            "exit_price": 40100.0,
            "size": 0.1,
            "pnl": 10.0,
            "exit_reason": "signal",
        }
    ]
    state.positions["ETH/EUR"] = OpenPositionState(
        symbol="ETH/EUR", side="long", size=1.0, entry_price=2500.0, entry_time="2024-01-01T01:00:00Z"
    )
    save_state(state, path)
    return path


def test_dashboard_renders_without_error_given_a_state_file(state_path, monkeypatch):
    monkeypatch.setenv("TRADING_STATE_PATH", str(state_path))
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception


def test_dashboard_shows_warning_when_no_state_file_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("TRADING_STATE_PATH", str(tmp_path / "does_not_exist.json"))
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception
    assert len(at.warning) == 1
