"""Fee, slippage, and funding cost model. Every backtest run through
Backtester uses this — there is no code path that produces a cost-free
result, per the hard rule that every backtest includes costs."""

from __future__ import annotations

from dataclasses import dataclass

from engine.types import Side


@dataclass
class CostModel:
    taker_fee_bps: float
    slippage_bps: float
    funding_bps_per_8h: float = 0.0

    def entry_fill_price(self, reference_price: float, side: Side) -> float:
        """Slippage is always adverse: buying (long entry / short exit) fills
        higher than reference, selling (short entry / long exit) fills lower."""
        slip = reference_price * (self.slippage_bps / 10_000)
        return reference_price + slip if side == Side.LONG else reference_price - slip

    def exit_fill_price(self, reference_price: float, side: Side) -> float:
        slip = reference_price * (self.slippage_bps / 10_000)
        return reference_price - slip if side == Side.LONG else reference_price + slip

    def fee(self, notional: float) -> float:
        return notional * (self.taker_fee_bps / 10_000)

    def funding_cost(self, notional: float, n_8h_periods: float) -> float:
        return notional * (self.funding_bps_per_8h / 10_000) * n_8h_periods
