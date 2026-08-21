import pytest

from engine.types import Side
from live.live_broker import LiveBroker, LiveTradingDisabledError


class FakeExchange:
    def __init__(self, api_key=None, secret=None):
        self.apiKey = api_key
        self.secret = secret
        self.orders: list[dict] = []

    def create_order(self, symbol, type, side, amount):
        order = {"symbol": symbol, "type": type, "side": side, "amount": amount}
        self.orders.append(order)
        return order


def test_refuses_order_when_trading_mode_is_paper():
    broker = LiveBroker(FakeExchange(api_key="k", secret="s"), trading_mode="paper")
    with pytest.raises(LiveTradingDisabledError, match="paper"):
        broker.place_market_order("BTC/EUR", Side.LONG, 0.01)


def test_refuses_order_when_live_but_no_credentials():
    broker = LiveBroker(FakeExchange(api_key=None, secret=None), trading_mode="live")
    with pytest.raises(LiveTradingDisabledError, match="API key"):
        broker.place_market_order("BTC/EUR", Side.LONG, 0.01)


def test_places_order_when_live_and_credentialed():
    exchange = FakeExchange(api_key="k", secret="s")
    broker = LiveBroker(exchange, trading_mode="live")
    result = broker.place_market_order("BTC/EUR", Side.LONG, 0.01)
    assert result["side"] == "buy"
    assert result["amount"] == 0.01
    assert len(exchange.orders) == 1


def test_short_side_maps_to_sell():
    exchange = FakeExchange(api_key="k", secret="s")
    broker = LiveBroker(exchange, trading_mode="live")
    result = broker.place_market_order("BTC/EUR", Side.SHORT, 0.01)
    assert result["side"] == "sell"


def test_trading_mode_defaults_to_paper_not_live():
    """Hard-rule check: the live-order path must default to inert."""
    import inspect

    from live import live_broker

    source = inspect.getsource(live_broker)
    assert 'os.environ.get("TRADING_MODE", "paper")' in source
