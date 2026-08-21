"""A deliberately non-final_evaluation module. Used by
tests/test_guard/test_holdout_guard.py to prove that guard/holdout_guard.py
rejects any caller other than evaluation/final_evaluation.py when the
"holdout" split is requested."""

from data.storage import load_split


def attempt_holdout_read(symbol: str, timeframe: str, data_dir, holdout_path):
    return load_split(symbol, timeframe, "holdout", data_dir=data_dir, holdout_path=holdout_path)
