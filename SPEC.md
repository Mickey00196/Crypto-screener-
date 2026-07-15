# Crypto Screener — Project Spec
*"Million-dollar looking" — premium feel, zero clutter, fast.*

## 1. Vision
A crypto screener that feels like it belongs in a top-tier trading terminal — not a spreadsheet of coins. Clean data density, instant filtering across thousands of tokens, and a UI polished enough that people screenshot it.

**Assumptions made (edit as needed):**
- Web app, desktop-first, responsive for tablet/mobile
- Free/public market data source to start (swap for premium later)
- Solo or small-team build, ship-fast mentality
- Covers spot markets to start (derivatives/futures as stretch)

---

## 2. Core Value Proposition
- Screen thousands of coins/tokens by market, on-chain, and technical criteria in real time
- Save/share custom screens
- Visual-first: sparklines, heatmaps, dominance charts — not just tables of numbers
- Feels instant — filtering shouldn't have a loading spinner
- Handles crypto-specific quirks: 24/7 markets, high volatility, thousands of low-cap tokens, multi-chain assets

---

## 3. Feature Set

### MVP (v1)
- [ ] Filter by: market cap, 24h/7d/30d % change, volume, circulating vs. total supply, exchange listings, chain/network
- [ ] Sortable results table with column customization
- [ ] Watchlist (save tickers, local storage or account-based)
- [ ] Basic coin detail view (price chart, key stats, links to explorers)
- [ ] Search by name/symbol/contract address with autocomplete
- [ ] Save/load custom screen presets
- [ ] Live-ish price updates (30-60s refresh, not full websocket yet)

### v2 — Differentiators
- [ ] Visual screener mode (scatter plot / heatmap of results, click to drill in)
- [ ] Technical filters: RSI, moving average crossovers, MACD, ATH/ATL proximity
- [ ] On-chain filters: holder count, whale concentration, liquidity depth, DEX volume
- [ ] Screen backtesting ("how would this screen have performed over 6mo/1yr?")
- [ ] Alerts (email/push/webhook when a token enters/exits a saved screen)
- [ ] Comparison view (select up to 4 tokens side-by-side)
- [ ] New listing / trending token detection
- [ ] **Technical Analysis Setup Detector** (see Section 4a below)

### v3 — Stretch
- [ ] AI-generated screen summaries ("this screen skews toward low-cap DeFi tokens")
- [ ] Community/shared screens (browse what others built)
- [ ] Wallet import + portfolio overlap analysis
- [ ] Rug-pull / scam-token risk flags (contract audit status, liquidity lock, mint authority)
- [ ] Real-time websocket price feeds
- [ ] Mobile app (React Native / PWA)

---

## 4. Design Principles (the "million-dollar" part)
1. **Data density without clutter** — use whitespace deliberately, not sparsely
2. **Motion with purpose** — subtle transitions on filter/sort, no gratuitous animation
3. **Dark mode as default** — crypto traders live in dark UIs; make it feel native, not inverted
4. **Monospace for numbers** — tabular figures align cleanly, feels "terminal-grade"
5. **One accent color for gains, one for losses** — consistent green/red, no rainbow dashboards elsewhere
6. **Empty states matter** — no blank screens; guide the user to their first screen
7. **Sub-200ms perceived filter response** — debounce + optimistic UI, even if data takes longer
8. **Respect the 24/7 nature** — no "market closed" assumptions baked into UI/UX like traditional stock tools

---

## 4a. Technical Analysis Setup Detector
The feature: for any coin, the screener surfaces its current chart "setup" (pattern + indicator confluence) and shows the most statistically likely next scenario — framed as probability, not certainty.

**How it should work:**
1. **Pattern recognition** — detect common chart setups algorithmically: breakout from consolidation, support/resistance retest, moving average crossover (golden/death cross), trendline break, higher-highs/higher-lows structure, RSI divergence, volume spike on breakout.
2. **Confluence scoring** — combine multiple signals (trend + momentum + volume) into a single setup label rather than firing on one indicator alone. E.g. "bullish breakout" only triggers if price + volume + RSI all agree.
3. **Scenario output, not a black-box prediction** — present it as: *"Setup: bullish flag breakout. Historically, this pattern with similar volume confirmation resolves upward ~X% of the time over the next N days (based on backtest of Y similar setups)."* Always show the sample size and win-rate honestly — this is pattern-matching against history, not a guarantee.
4. **Confidence tiers** — Low / Medium / High confluence, based on how many signals agree and how clean the pattern is.
5. **Screener integration** — let users filter for "coins currently showing a bullish setup" or "coins near a key resistance retest" as a filter criterion, not just a per-coin detail view.

**Suggested signals to combine:**
| Category | Signals |
|---|---|
| Trend | Moving average alignment (20/50/200), higher-highs/higher-lows structure |
| Momentum | RSI level + divergence, MACD crossover/histogram |
| Volume | Volume vs. 20-day average, volume on breakout candles |
| Structure | Support/resistance proximity, consolidation range breakout, trendline breaks |

**Additional bullish/"push higher" indicators worth backtesting:**
| Indicator | What it flags | Why it's relevant |
|---|---|---|
| **Volume spike + price breakout** | Volume ≥ 1.5-2x the 20-day average on the breakout candle | Confirms real buying pressure, not a low-volume fakeout |
| **On-Balance Volume (OBV) rising** | OBV trending up while price consolidates | Accumulation happening before price confirms — often a leading signal |
| **Volume-Weighted Average Price (VWAP) reclaim** | Price crosses back above VWAP with volume | Common short-term bullish trigger, widely watched by traders |
| **Accumulation/Distribution Line (A/D)** | A/D rising alongside price | Confirms volume is supporting the trend, not diverging from it |
| **Relative Volume (RVOL)** | Current volume vs. average volume for that time of day | Flags unusual interest — often precedes a move |
| **Bollinger Band squeeze + expansion** | Bands narrow (low volatility) then expand with volume | Classic setup before a directional breakout |
| **Higher low on declining volume, breakout on rising volume** | Volume dries up during pullback, then surges on the push higher | A well-known bullish continuation signature |
| **Golden Cross (50MA crosses above 200MA)** | Medium/long-term trend shift | Backtest well on higher timeframes, less noisy than short MAs |
| **RSI bullish divergence + volume confirmation** | Price makes lower low, RSI makes higher low, then volume picks up on the reversal | Stronger signal than RSI divergence alone |
| **Funding rate / open interest shifts (crypto-specific)** | Funding rate resetting from negative to neutral/positive with rising OI | Signals short squeezes or fresh long positioning — crypto-derivatives-specific edge |
| **Exchange netflow (crypto-specific, on-chain)** | Coins flowing off exchanges | Often read as reduced sell pressure / accumulation |

**Backtesting approach for these:**
- For each indicator (and combinations), backtest against historical data: "when X occurred, price was up Y% after N days, Z% of the time, across M historical occurrences"
- Weight volume-based signals heavily — volume confirmation is one of the most consistently backtested factors for reducing false breakouts across both stock and crypto TA research
- Track combos, not just single signals — e.g. "volume spike + OBV rising + RVOL > 2" as a labeled composite setup, separately backtested from any single signal
- Store win-rate, average move size, and sample count per indicator/combo so the confidence tier (Low/Medium/High) can be data-driven, not arbitrary
- Re-run backtests periodically (e.g. monthly) as more data accumulates — win rates can drift, especially in crypto

**Implementation approach:**
- Compute indicators server-side (nightly or intraday batch) using `pandas-ta` or `ta-lib` on OHLC data
- Backtest each pattern type against historical data to generate the "resolves upward X% of the time" stat — store this as a static/updated-periodically lookup, not computed live
- Surface result as a labeled setup + confidence tier + probability, with a link to "why" (which signals fired)

**Important framing note:** this is a *statistical pattern-matching tool*, not financial advice or a guaranteed prediction. The UI copy should always communicate uncertainty (probabilities, sample sizes, "historically" language) rather than definitive calls like "will go up." This protects users from over-trusting the signal and keeps the tool honest about what TA can and can't do.

---

## 5. Suggested Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js (React) + Tailwind CSS | Fast iteration, great DX, easy deploy |
| UI components | shadcn/ui + Recharts/Lightweight Charts | Polished defaults, customizable |
| State/data fetching | TanStack Query | Caching, background refetch |
| Backend | FastAPI (Python) or Node/Express | Python if doing quant/on-chain analysis server-side |
| Database | PostgreSQL (screens, users, watchlists) + Redis (hot price cache) | Relational for structured data, Redis for fast-changing prices |
| Market data | Start: CoinGecko (free tier) → Later: CoinMarketCap Pro / CryptoCompare / Kaiko | Free to prototype, paid for higher rate limits & reliability |
| On-chain data | Etherscan/BscScan-type explorers, or Covalent/Moralis for multi-chain | Needed for holder counts, liquidity, contract data |
| Auth | Clerk or Supabase Auth | Fast to integrate, don't build this yourself |
| Hosting | Vercel (frontend) + Railway/Render (backend+DB) | Low-ops, scales fine for MVP |
| Charts | Lightweight Charts (TradingView's OSS lib) | Industry-standard candlestick/line charts |

---

## 6. Data Considerations
- Crypto markets never close — batch jobs need to run continuously, not on a market-hours schedule
- Real-time data is expensive at scale — decide early: 30-60s polling is fine for MVP, websockets later
- Cache aggressively; screener queries against a warm cache, not live API calls per filter change
- Token universe is huge (20,000+ coins on CoinGecko alone) — decide scope early: top 500 by market cap? Top 1000? All listed?
- Watch for data quality issues: fake volume, delisted tokens, duplicate tickers across chains — plan a filtering/cleaning step
- Multi-chain tokens (same project, different contract per chain) need careful data modeling

---

## 7. Architecture Sketch
```
[Market Data API] → [Ingestion job] → [Postgres: tokens, market data, historical prices]
[On-chain API]    →        ↓                    ↓
                    [Redis: hot price cache]  [FastAPI screening endpoint]
                                                        ↓
                                  [Next.js frontend — filter UI, results, charts]
                                                        ↓
                                    [User DB: watchlists, saved screens, alerts]
```

---

## 8. Roadmap (suggested)
| Phase | Timeframe | Goal |
|---|---|---|
| Phase 0 | Week 1 | Data pipeline: pull + store market data for top 500-1000 coins |
| Phase 1 | Weeks 2-3 | MVP filter UI + results table, deployed |
| Phase 2 | Week 4 | Watchlists, saved screens, polish pass |
| Phase 3 | Weeks 5-6 | Technical filters + on-chain data + charting |
| Phase 4 | Ongoing | Alerts, backtesting, risk flags, visual screener mode |

---

## 9. Open Questions
- Free tier limits vs. paid — will this be a product with pricing, or a personal tool?
- Which universe of coins? (Top 500 by market cap? Specific chains only? Include memecoins?)
- Account system needed for MVP, or local-storage-only watchlists first?
- Is on-chain data (holder count, liquidity, contract risk) in scope for MVP or v2+?

---

## 10. Success Criteria for "Million-Dollar Looking"
- A stranger seeing a screenshot assumes it's a funded startup, not a side project
- Filtering feels instant even under load, even with a 24/7 constantly-moving market
- Someone could demo this in an investor pitch without flinching at the UI
