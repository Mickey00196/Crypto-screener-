"""Chart-setup scanner: key levels, rising channel, and the scenario
(sweep / breakout / retest) they imply. Entry point: setups.analyze."""

from setups.channel import Channel, fit_rising_channel
from setups.levels import Level, Pivot, build_levels, find_pivots, round_levels
from setups.scenario import Setup, analyze, describe

__all__ = [
    "Channel",
    "Level",
    "Pivot",
    "Setup",
    "analyze",
    "build_levels",
    "describe",
    "find_pivots",
    "fit_rising_channel",
    "round_levels",
]
