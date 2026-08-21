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
COPY scripts ./scripts

RUN pip install --no-cache-dir .

# Hard rule: TRADING_MODE must default to paper. Override deliberately at
# deploy time (e.g. Railway service variables) with real keys to go live.
ENV TRADING_MODE=paper

CMD ["python", "scripts/run_paper_trading.py"]
