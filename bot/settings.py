"""Typed, config-driven settings. No trading parameters are hardcoded in strategy
or engine code — everything lives in config/settings.yaml and is loaded here."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

BOT_ROOT = Path(__file__).resolve().parent
CONFIG_DIR = BOT_ROOT / "config"
DEFAULT_SETTINGS_PATH = CONFIG_DIR / "settings.yaml"
DEFAULT_HOLDOUT_PATH = CONFIG_DIR / "holdout.yaml"


class CostsConfig(BaseModel):
    taker_fee_bps: float
    maker_fee_bps: float
    slippage_bps: float
    funding_bps_per_8h: float = 0.0


class RiskDefaults(BaseModel):
    max_risk_per_trade_pct: float
    max_position_pct: float
    max_concurrent_positions: int
    daily_loss_limit_pct: float
    max_drawdown_kill_switch_pct: float


class Settings(BaseModel):
    trading_mode: Literal["paper", "live"] = "paper"
    pairs: list[str]
    timeframes: list[str]
    exchange_execution: str
    exchange_research: str
    train_frac: float
    val_frac: float
    costs: CostsConfig
    risk: RiskDefaults


def load_settings(path: Path | None = None) -> Settings:
    path = path or DEFAULT_SETTINGS_PATH
    with open(path) as f:
        raw = yaml.safe_load(f)
    return Settings(**raw)
