"""REAL order placement via ccxt. This is the hard rule's enforcement point:
every method here refuses to run unless TRADING_MODE=live AND the exchange
client has real API credentials configured — an accidental call fails
loudly with LiveTradingDisabledError instead of silently doing nothing or,
worse, silently placing a real order. TRADING_MODE defaults to "paper"
everywhere in this repo (settings.py, .env.example)."""

from __future__ import annotations

import os
from typing import Protocol

from engine.types import Side


class LiveTradingDisabledError(Exception):
    pass


class OrderExchange(Protocol):
    apiKey: str | None
    secret: str | None

    def create_order(self, symbol: str, type: str, side: str, amount: float) -> dict: ...


class LiveBroker:
    def __init__(self, exchange: OrderExchange, trading_mode: str):
        self.exchange = exchange
        self.trading_mode = trading_mode

    def _assert_live_enabled(self) -> None:
        if self.trading_mode != "live":
            raise LiveTradingDisabledError(
                f"refusing to place a real order: TRADING_MODE={self.trading_mode!r}, not 'live'. "
                "Flip TRADING_MODE=live deliberately, with real exchange keys, to enable this."
            )
        if not getattr(self.exchange, "apiKey", None) or not getattr(self.exchange, "secret", None):
            raise LiveTradingDisabledError(
                "TRADING_MODE=live but no API key/secret configured on the exchange client."
            )

    def place_market_order(self, symbol: str, side: Side, size: float) -> dict:
        self._assert_live_enabled()
        ccxt_side = "buy" if side == Side.LONG else "sell"
        return self.exchange.create_order(symbol, type="market", side=ccxt_side, amount=size)

    @classmethod
    def from_env(cls) -> LiveBroker:
        import ccxt

        trading_mode = os.environ.get("TRADING_MODE", "paper")
        api_key = os.environ.get("BITVAVO_API_KEY")
        api_secret = os.environ.get("BITVAVO_API_SECRET")
        config: dict = {"enableRateLimit": True}
        if api_key and api_secret:
            config["apiKey"] = api_key
            config["secret"] = api_secret
        exchange = ccxt.bitvavo(config)
        return cls(exchange, trading_mode)
