"""Parquet-backed OHLCV storage. `load_split` is the ONLY sanctioned way to
read a chronological split — it is the gated entrypoint that enforces the
holdout guard (see guard/holdout_guard.py). Never read data/processed/*.parquet
directly from evaluation/optimization/strategy code; use load_split."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from guard.holdout_guard import _load_boundaries, check_caller, enforce_dataframe_boundary

BOT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = BOT_ROOT / "data" / "processed"
DEFAULT_HOLDOUT_PATH = BOT_ROOT / "config" / "holdout.yaml"

Split = Literal["train", "val", "train_val", "holdout"]
_VALID_SPLITS = {"train", "val", "train_val", "holdout"}


def _symbol_to_dirname(symbol: str) -> str:
    return symbol.replace("/", "_")


def save_ohlcv(df: pd.DataFrame, symbol: str, timeframe: str, data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    out_dir = Path(data_dir) / _symbol_to_dirname(symbol)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{timeframe}.parquet"
    df.to_parquet(out_path, index=False)
    return out_path


def load_raw(symbol: str, timeframe: str, data_dir: Path = DEFAULT_DATA_DIR) -> pd.DataFrame:
    """Internal use only (e.g. by data/splits.py to compute boundaries).
    Strategy/engine/optimization/evaluation code must use load_split instead."""
    path = Path(data_dir) / _symbol_to_dirname(symbol) / f"{timeframe}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — has data/fetch_binance.py or fetch_bitvavo.py been run "
            "for this symbol/timeframe yet?"
        )
    return pd.read_parquet(path)


def load_split(
    symbol: str,
    timeframe: str,
    split: Split,
    data_dir: Path = DEFAULT_DATA_DIR,
    holdout_path: Path = DEFAULT_HOLDOUT_PATH,
) -> pd.DataFrame:
    """The sole sanctioned entrypoint for reading a chronological data split.
    Raises guard.holdout_guard.HoldoutBreachError if `split="holdout"` is
    requested from anywhere other than evaluation/final_evaluation.py."""
    if split not in _VALID_SPLITS:
        raise ValueError(f"split must be one of {_VALID_SPLITS}, got {split!r}")

    check_caller(split)

    df = load_raw(symbol, timeframe, data_dir)
    boundaries = _load_boundaries(holdout_path)[symbol][timeframe]
    train_end = pd.Timestamp(boundaries["train_end"])
    val_end = pd.Timestamp(boundaries["val_end"])

    if split == "train":
        out = df[df["timestamp"] < train_end]
    elif split == "val":
        out = df[(df["timestamp"] >= train_end) & (df["timestamp"] < val_end)]
    elif split == "train_val":
        out = df[df["timestamp"] < val_end]
    else:  # holdout
        out = df[df["timestamp"] >= val_end]

    enforce_dataframe_boundary(
        out, symbol, timeframe, allow_holdout=(split == "holdout"), holdout_path=holdout_path
    )
    return out.reset_index(drop=True)
