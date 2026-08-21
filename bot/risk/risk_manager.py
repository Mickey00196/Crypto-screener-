"""Risk management — deliberately a SEPARATE module from strategies/, per
the brief's Phase 3 requirement. A strategy only says "long/flat/short"; this
module decides how much to risk, where the stop/target go, how many
positions may run concurrently, and when to stop trading altogether (daily
loss limit, drawdown kill switch). Satisfies engine.types.RiskManagerLike."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from engine.types import Position, Side, SizeDecision
from indicators.trend import atr


@dataclass
class RiskConfig:
    max_risk_per_trade_pct: float
    max_position_pct: float
    max_concurrent_positions: int
    daily_loss_limit_pct: float
    max_drawdown_kill_switch_pct: float
    atr_period: int = 14
    atr_stop_multiplier: float = 2.0
    atr_target_multiplier: float = 3.0  # target = stop_distance * (target/stop), e.g. 3/2 = 1.5 R:R

    @classmethod
    def from_settings(cls, risk_settings, atr_period=14, atr_stop_multiplier=2.0, atr_target_multiplier=3.0):
        return cls(
            max_risk_per_trade_pct=risk_settings.max_risk_per_trade_pct,
            max_position_pct=risk_settings.max_position_pct,
            max_concurrent_positions=risk_settings.max_concurrent_positions,
            daily_loss_limit_pct=risk_settings.daily_loss_limit_pct,
            max_drawdown_kill_switch_pct=risk_settings.max_drawdown_kill_switch_pct,
            atr_period=atr_period,
            atr_stop_multiplier=atr_stop_multiplier,
            atr_target_multiplier=atr_target_multiplier,
        )


class RiskManager:
    """Implements engine.types.RiskManagerLike."""

    def __init__(self, config: RiskConfig):
        self.config = config
        self._current_day: pd.Timestamp | None = None
        self._day_start_equity: float | None = None

    def _update_daily_tracking(self, current_time, equity: float) -> None:
        day = pd.Timestamp(current_time).normalize()
        if self._current_day is None or day != self._current_day:
            self._current_day = day
            self._day_start_equity = equity

    def _daily_loss_breached(self, equity: float) -> bool:
        if not self._day_start_equity or self._day_start_equity <= 0:
            return False
        loss_pct = (self._day_start_equity - equity) / self._day_start_equity * 100
        return loss_pct >= self.config.daily_loss_limit_pct

    def decide(
        self,
        side: Side,
        symbol: str,
        df_so_far: pd.DataFrame,
        equity: float,
        open_positions: dict[str, Position],
    ) -> SizeDecision:
        if len(df_so_far) == 0:
            return SizeDecision(size=0)

        current_time = df_so_far["timestamp"].iloc[-1]
        self._update_daily_tracking(current_time, equity)
        if self._daily_loss_breached(equity):
            return SizeDecision(size=0)

        if len(open_positions) >= self.config.max_concurrent_positions:
            return SizeDecision(size=0)

        if len(df_so_far) < self.config.atr_period + 1:
            return SizeDecision(size=0)  # not enough data to compute a volatility-scaled stop

        atr_series = atr(df_so_far, self.config.atr_period)
        current_atr = atr_series.iloc[-1]
        if pd.isna(current_atr) or current_atr <= 0:
            return SizeDecision(size=0)

        reference_price = float(df_so_far["close"].iloc[-1])
        if reference_price <= 0:
            return SizeDecision(size=0)

        stop_distance = current_atr * self.config.atr_stop_multiplier
        target_distance = current_atr * self.config.atr_target_multiplier
        if side == Side.LONG:
            stop_price = reference_price - stop_distance
            take_profit_price = reference_price + target_distance
        else:
            stop_price = reference_price + stop_distance
            take_profit_price = reference_price - target_distance

        risk_amount = equity * (self.config.max_risk_per_trade_pct / 100)
        size_by_risk = risk_amount / stop_distance

        max_notional = equity * (self.config.max_position_pct / 100)
        size_by_cap = max_notional / reference_price

        size = min(size_by_risk, size_by_cap)
        if size <= 0:
            return SizeDecision(size=0)

        return SizeDecision(size=size, stop_price=stop_price, take_profit_price=take_profit_price)

    def should_halt(self, equity_history: list[float], initial_capital: float) -> bool:
        if not equity_history:
            return False
        peak = max(equity_history)
        current = equity_history[-1]
        if peak <= 0:
            return False
        drawdown_pct = (peak - current) / peak * 100
        return drawdown_pct >= self.config.max_drawdown_kill_switch_pct
