from optimization.grid import sample_configs


def test_sample_configs_returns_requested_count_when_space_is_large():
    space = {"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]}
    configs = sample_configs(space, n_configs=10, seed=42)
    assert len(configs) == 10


def test_sample_configs_has_no_duplicates():
    space = {"a": [1, 2, 3], "b": [10, 20, 30]}
    configs = sample_configs(space, n_configs=9, seed=1)  # full space = 9
    seen = {tuple(sorted(c.items())) for c in configs}
    assert len(seen) == len(configs)


def test_sample_configs_caps_at_full_cartesian_size():
    space = {"a": [1, 2], "b": [10, 20]}  # only 4 possible combos
    configs = sample_configs(space, n_configs=50, seed=1)
    assert len(configs) == 4


def test_sample_configs_deterministic_given_seed():
    space = {"a": [1, 2, 3, 4], "b": [10, 20, 30, 40]}
    a = sample_configs(space, n_configs=5, seed=7)
    b = sample_configs(space, n_configs=5, seed=7)
    assert a == b


def test_sample_configs_different_seeds_can_differ():
    space = {"a": list(range(20)), "b": list(range(20))}
    a = sample_configs(space, n_configs=5, seed=1)
    b = sample_configs(space, n_configs=5, seed=2)
    assert a != b
