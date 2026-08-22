FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY settings.py ./
COPY config ./config
COPY guard ./guard
COPY data ./data
COPY engine ./engine
COPY indicators ./indicators
COPY strategies ./strategies
COPY risk ./risk
COPY evaluation ./evaluation
COPY optimization ./optimization
COPY live ./live
COPY dashboard ./dashboard
COPY scripts ./scripts

RUN pip install --no-cache-dir .

# Verified building successfully on Railway (Railpack/BuildKit) after the
# `dashboard/` COPY fix above — see FINDINGS.md for the network-reachability
# results that build was used to diagnose (api.binance.com returns HTTP 451
# from Railway's us-west2 region; api.bitvavo.com is being checked).

# Hard rule: TRADING_MODE must default to paper. Override deliberately at
# deploy time (e.g. Railway service variables) with real keys to go live.
ENV TRADING_MODE=paper

CMD ["python", "scripts/run_paper_trading.py"]
