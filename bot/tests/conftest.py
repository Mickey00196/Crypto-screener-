import pytest

from data.splits import compute_split_boundaries, write_holdout_config
from data.storage import save_ohlcv
from data.synthetic import generate_synthetic_ohlcv


@pytest.fixture
def populated_store(tmp_path):
    """A small synthetic dataset written to a tmp Parquet store, with a
    matching config/holdout.yaml-shaped file at a tmp path. Used by guard
    and storage tests so they never touch the real (nonexistent) data dir."""
    data_dir = tmp_path / "processed"
    holdout_path = tmp_path / "holdout.yaml"
    symbol, timeframe = "BTC/USDT", "1h"
    df = generate_synthetic_ohlcv(n_bars=500, timeframe=timeframe, regime="mixed", seed=1)
    save_ohlcv(df, symbol, timeframe, data_dir=data_dir)
    boundaries = {symbol: {timeframe: compute_split_boundaries(df, 0.6, 0.2)}}
    write_holdout_config(boundaries, holdout_path)
    return {
        "data_dir": data_dir,
        "holdout_path": holdout_path,
        "symbol": symbol,
        "timeframe": timeframe,
        "df": df,
    }
