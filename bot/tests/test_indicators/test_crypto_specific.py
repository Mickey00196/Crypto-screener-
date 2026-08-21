import pandas as pd
import pytest

from indicators.crypto_specific import (
    basis,
    exchange_netflow,
    funding_rate,
    long_short_ratio,
    open_interest_change,
)


def test_all_crypto_specific_indicators_fail_loudly_not_silently():
    df = pd.DataFrame({"close": [1.0, 2.0]})
    with pytest.raises(NotImplementedError, match="futures"):
        funding_rate(df)
    with pytest.raises(NotImplementedError, match="futures"):
        open_interest_change(df)
    with pytest.raises(NotImplementedError, match="futures"):
        long_short_ratio(df)
    with pytest.raises(NotImplementedError, match="spot and perpetual"):
        basis(df, df)
    with pytest.raises(NotImplementedError, match="on-chain"):
        exchange_netflow(df)
