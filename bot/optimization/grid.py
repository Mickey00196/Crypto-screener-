"""Bounded, seeded parameter sampler — deliberately NOT a full factorial
grid search, which would either blow past the anti-overfit budget (max 50
configs/family) or be too coarse to be useful. Sampling without replacement
via rejection sampling keeps every returned config unique and the whole
process deterministic given the same seed, so a sweep is reproducible."""

from __future__ import annotations

import random
from typing import Any


def sample_configs(param_space: dict[str, list[Any]], n_configs: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    keys = list(param_space.keys())
    max_possible = 1
    for v in param_space.values():
        max_possible *= len(v)
    target = min(n_configs, max_possible)

    seen: set[tuple] = set()
    configs: list[dict[str, Any]] = []
    max_attempts = target * 100 + 100
    attempts = 0
    while len(configs) < target and attempts < max_attempts:
        attempts += 1
        combo = tuple(rng.choice(param_space[k]) for k in keys)
        if combo in seen:
            continue
        seen.add(combo)
        configs.append(dict(zip(keys, combo, strict=True)))
    return configs
