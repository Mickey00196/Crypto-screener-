import pytest

from data.storage import load_split
from guard.holdout_guard import HoldoutBreachError, enforce_dataframe_boundary
from tests.fixtures import rogue_caller


def test_rogue_caller_cannot_read_holdout(populated_store):
    with pytest.raises(HoldoutBreachError):
        rogue_caller.attempt_holdout_read(
            populated_store["symbol"],
            populated_store["timeframe"],
            populated_store["data_dir"],
            populated_store["holdout_path"],
        )


def test_load_split_holdout_rejected_when_called_directly_from_test(populated_store):
    with pytest.raises(HoldoutBreachError):
        load_split(
            populated_store["symbol"],
            populated_store["timeframe"],
            "holdout",
            data_dir=populated_store["data_dir"],
            holdout_path=populated_store["holdout_path"],
        )


def test_train_and_val_readable_from_any_caller(populated_store):
    train = load_split(
        populated_store["symbol"],
        populated_store["timeframe"],
        "train",
        data_dir=populated_store["data_dir"],
        holdout_path=populated_store["holdout_path"],
    )
    val = load_split(
        populated_store["symbol"],
        populated_store["timeframe"],
        "val",
        data_dir=populated_store["data_dir"],
        holdout_path=populated_store["holdout_path"],
    )
    train_val = load_split(
        populated_store["symbol"],
        populated_store["timeframe"],
        "train_val",
        data_dir=populated_store["data_dir"],
        holdout_path=populated_store["holdout_path"],
    )
    assert len(train) > 0
    assert len(val) > 0
    assert len(train_val) == len(train) + len(val)
    assert train["timestamp"].max() < val["timestamp"].min()


def test_load_split_rejects_unknown_split_value(populated_store):
    with pytest.raises(ValueError):
        load_split(
            populated_store["symbol"],
            populated_store["timeframe"],
            "bogus",
            data_dir=populated_store["data_dir"],
            holdout_path=populated_store["holdout_path"],
        )


def test_enforce_dataframe_boundary_blocks_past_holdout(populated_store):
    df = populated_store["df"]  # full series, extends past the holdout boundary
    with pytest.raises(HoldoutBreachError):
        enforce_dataframe_boundary(
            df,
            populated_store["symbol"],
            populated_store["timeframe"],
            allow_holdout=False,
            holdout_path=populated_store["holdout_path"],
        )


def test_enforce_dataframe_boundary_allows_with_explicit_flag(populated_store):
    df = populated_store["df"]
    # Does not raise — this is the one legitimate call shape, used only from
    # evaluation/final_evaluation.py in real code.
    enforce_dataframe_boundary(
        df,
        populated_store["symbol"],
        populated_store["timeframe"],
        allow_holdout=True,
        holdout_path=populated_store["holdout_path"],
    )
