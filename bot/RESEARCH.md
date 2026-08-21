# Phase 0 — Research

This document surveys candidate strategy families and the published evidence on
mainstream technical indicators, then picks the three families implemented in
this repo. It is written before any strategy code, per the build brief.

**A note on sourcing.** Citations below come from a mix of peer-reviewed /
working papers (cited by name/venue where the search surfaced them) and
practitioner sources (blogs, vendor education pages, TradingView write-ups).
Practitioner sources are marked `[practitioner]` and should be weighted lower —
they are useful for describing *what people commonly do* and *rough parameter
conventions*, not as evidence of a real edge. Numbers quoted from them (e.g.
"82% of band touches preceded reversals") are frequently unsourced marketing
copy and are called out as such, not treated as fact.

---

## 1. The core tension in the Definition of Done

Before picking families, it's worth stating plainly why this is hard. The
brief requires **simultaneously**: win rate ≥55%, profit factor ≥1.3,
positive expectancy net of costs, max drawdown ≤20%, Sortino ≥1.0, ≥200
trades, ≥3 walk-forward windows, positive expectancy in both bull and
chop/bear regimes, and beating buy-and-hold risk-adjusted.

Two well-documented archetypes fail this combination in opposite ways:

- **Classic trend-following** (Donchian/turtle-style breakout, time-series
  momentum) has a well-documented edge — Moskowitz, Ooi & Pedersen (2012),
  *"Time Series Momentum,"* show a persistent 12-month trend effect with
  significant abnormal returns across 58 futures markets, 1985-2009 — but it
  typically clears win rate **30-45%** with average winners 3-5x average
  losers (favorable R:R, low win rate) [practitioner + academic]. That fails
  the ≥55% win-rate gate outright, however good its PF/Sortino may be.
- **Naive mean-reversion** (RSI oversold/overbought against Bollinger Bands)
  can post high win rates in the 60-80% range in ranging conditions, but the
  average win is small and the average loss (a regime change that keeps
  trending against the position) is large and fat-tailed. As one practitioner
  source bluntly puts it: *"a 0.4% bounce can vanish after entry fees, exit
  fees, spread, and slippage — if your edge only exists before costs, it
  doesn't exist."* This is exactly the failure mode the brief's example (90%
  win rate, 3% TP / 30% SL) warns about — it tends to fail PF and max-drawdown
  even when win rate clears 55%.

So neither archetype in its pure form is likely to pass every gate at once.
The strategies chosen below deliberately hybridize: use a trend/regime filter
to raise the reliability of entries (lifting win rate) while keeping a
volatility-scaled, *defined* stop/target (protecting R:R and tail risk) rather
than letting either a naive breakout or a naive oscillator trade unfiltered.
Given this tension, the honest expectation set going into Phase 4 is that
**FINDINGS.md (the escape hatch) is a live, non-embarrassing possible
outcome** — not a fallback of last resort.

---

## 2. Candidate strategy families

### 2.1 Trend / momentum breakout (Donchian, MA cross + volatility filter)
- **Typical win rate / R:R**: ~30-45% win rate, 3-5x avg-win-to-avg-loss
  [practitioner sources on Donchian backtests]. A 20/55-period Donchian
  ("Turtle"-style) system on BTC daily bars since 2017 is reported to have
  produced positive returns across the 2017 bull, 2018 bear, 2020-21 bull,
  2022 bear, and 2023+ recovery — i.e. regime-robust, if low win-rate
  [practitioner].
- **Academic anchor**: Moskowitz, Ooi & Pedersen (2012), *Time Series
  Momentum*, Journal of Financial Economics — trend persists ~1-12 months
  then partially reverses; effect is well-replicated out-of-sample across
  asset classes and considered one of the more robust anomalies in the
  literature.
- **Regime**: works in trending markets; the classic failure mode is chop
  (repeated false breakouts, "whipsaw").
- **Data needs**: OHLCV only. **Capacity**: high (works at daily/4h/1h on
  liquid pairs).
- **Verdict for this brief**: fails the win-rate gate in its pure form; a
  candidate only if hybridized with a mean-reversion-style entry trigger to
  raise win rate (see Family 2/3 below).

### 2.2 Mean reversion (Bollinger/z-score, pairs/stat-arb)
- **Typical win rate / R:R**: reported 60-80%+ win rate in range-bound
  conditions [practitioner], but R:R is often <1 (small target, wide or
  late stop), and tail risk is significant when a "reversion" turns into a
  regime change (trend continuation through the band).
- **Regime**: works in chop/range; the classic failure mode is a strong trend
  (repeatedly buying dips into a downtrend, or fading a breakout that keeps
  going).
- **Data needs**: OHLCV; pairs/stat-arb variants need a cointegrated pair and
  are out of scope here (no cross-asset universe deep enough yet).
- **Verdict**: a plausible win-rate-≥55% contributor **only** when gated by a
  trend filter that restricts entries to pullback-in-trend rather than
  fade-the-trend (Family 1 below).

### 2.3 Volatility regime filters (ATR, realised vol, regime switching)
- Not a standalone entry signal — used as a **filter/sizing** input across all
  three chosen families (position sizing, stop/target distance). ADX is the
  most commonly cited regime-classification tool: *"ADX's best use is as a
  regime filter: deciding whether the market is in a trend (high ADX, favor
  trend following) or in a range (low ADX, favor reversion oscillators)"*
  [practitioner], with ADX > 20-25 conventionally read as "trending" and
  <20 as "ranging/choppy." No peer-reviewed study specifically validating
  these thresholds turned up in this search; treated as a widely-used
  heuristic, not proven edge, hence used only as a filter (per the
  brief's own combination rules), never as a standalone trigger.

### 2.4 Funding rate and basis carry
- **Reported returns**: a delta-neutral long-spot/short-perpetual funding
  carry strategy using 3 years of tick data is reported to achieve ~16%
  annualized return, Sharpe 6.1, max drawdown <2% [SSRN preprint, Chan
  (2025), *Leveraged BTC Funding Carry Algorithm*] — a fundamentally
  different risk/return shape (market-neutral, funding income) than a
  directional strategy, so its win-rate/PF framing doesn't map onto this
  brief's gates directly (it's closer to "always in a trade, harvesting a
  spread" than "win/lose directional trades").
  Note: `bot/indicators/crypto_specific.py`'s funding-rate/OI stubs
  document that Binance/Bitvavo *spot* OHLCV (what this pass fetches) has no
  funding-rate field — that requires a perpetual-futures data feed, which is
  out of scope for the reduced pass but flagged as the natural next data
  source to add.
- **Regime**: works regardless of directional trend as long as funding stays
  persistently one-sided; **failure mode**: funding flips sign in a violent
  reversal and the "safe" carry position can face liquidation risk on the
  leveraged leg if not perfectly hedged, and the strategy has near-zero
  correlation to the directional metrics (win rate/R:R) this brief measures.
- **Verdict**: not selected for this pass — no funding-rate data source is
  wired up yet (spot data only), and it doesn't produce the kind of
  win-rate/PF trade stream the Definition of Done is built around.

### 2.5 Order-book imbalance / microstructure
- **Evidence**: order flow imbalance is described as *"the strongest simple
  predictor of the next short-horizon price move"* with alpha that *"decays
  fast... a forward signal with a short but usable half-life,"* useful over
  "tens of seconds" to "10-30 seconds" horizons [practitioner/quant-blog
  sources on crypto perp microstructure].
- **Regime**: horizon-specific — this is a market-making/HFT signal, not a
  1h/4h swing signal.
- **Data needs**: L2/L3 order-book snapshots or tick-level trade data — not
  available from the OHLCV-only pipeline this pass builds.
- **Verdict**: not selected — wrong timeframe for this brief's 1h/4h scope,
  and the required data isn't fetched. Documented as a legitimate future
  direction requiring a different data source and a sub-minute execution
  stack.

### 2.6 Supervised ML classifier (triple-barrier labelling)
- **Method**: López de Prado (2018), *Advances in Financial Machine
  Learning* — the triple-barrier method labels each observation by which of
  three barriers (profit-take, stop-loss, or a time-based vertical barrier)
  is touched first, replacing naive fixed-horizon return labels with
  path-dependent, volatility-adjusted ones. Has been adapted specifically to
  crypto pair-trading in at least one 2024 paper (Enhanced
  Genetic-Algorithm-Driven Triple Barrier Labeling, *Mathematics* / MDPI).
- **Regime**: label quality directly encodes the strategy's own stop/target,
  so it inherits whatever regime-robustness the barrier design has.
- **Failure mode**: López de Prado's own broader point (cited repeatedly
  across sources) is that *"standard data science methodologies, when applied
  to quantitative finance, routinely lead to backtest overfitting and the
  deployment of false strategies"* — i.e. this family is *more* prone to
  overfitting than rule-based strategies precisely because it has more
  degrees of freedom (features, model hyperparameters, labelling
  hyperparameters), all consuming the anti-overfit budget the brief caps at
  50 configs/family.
- **Verdict**: not selected for the first 3 implemented families, specifically
  *because* of the parameter-budget/overfitting risk relative to a reduced
  2-pair, 2-timeframe dataset — a classifier with even a modest feature set
  can burn the 50-config budget on model hyperparameters alone before any
  feature-engineering search happens. Worth revisiting once the 5-pair/4-tf
  dataset is available and gives the model enough independent samples.

### 2.7 Session / time-of-day effects
- **Evidence**: mixed and asset-specific. One line of research finds
  *"Bitcoin returns on Mondays are significantly higher than those on other
  days... though not universal across cryptocurrencies"* and, at hourly
  resolution, that the effect concentrates in the *"23:00-00:00 UTC window on
  Sunday night"* for liquid assets. Volume/volatility are reported higher
  during US equity-market hours than European or Asian hours.
- **Regime**: this is a *filter/timing overlay*, not a standalone
  directional strategy — it says nothing about entry trigger or exit.
- **Verdict**: not selected as a standalone family (too thin an edge, mostly
  a volume/liquidity artifact); could be layered later as a session filter
  (e.g. avoid opening new positions in known low-liquidity windows) but adds
  parameter surface this pass's budget doesn't spend on it.

### 2.8 Cross-asset or on-chain signals
- **Data needs**: on-chain data (exchange netflow, active addresses, miner
  flows) or a cross-asset universe beyond BTC/ETH (this pass only fetches 2
  pairs). Neither is available in this pass's pipeline.
- **Verdict**: not selected — no data source wired up. Documented as a future
  extension once the 5-pair universe is built out (cross-asset momentum
  rank/rotation becomes feasible with more pairs) or an on-chain data
  provider is integrated.

---

## 3. Indicator evidence table (Phase 2b indicators)

| Indicator | Category | Out-of-sample evidence | Verdict |
|---|---|---|---|
| EMA/SMA cross | Trend | Component of Time Series Momentum-style effects (Moskowitz et al.); simple crossovers alone show mixed/inconsistent out-of-sample edge in equity studies, but remain a reasonable **trend-direction** proxy | Use as trend filter, not standalone trigger |
| MACD | Trend/Momentum | Mathematically a difference of two EMAs (a smoothed version of EMA cross) — largely redundant with EMA cross; academic technical-analysis reviews note many oscillators are repackagings of the same underlying moving-average information | Redundant with EMA cross if both used — pick one |
| ADX/DMI | Trend (regime) | No peer-reviewed validation surfaced; widely used as a **regime classifier** (trending vs. ranging) via the ADX>20-25 heuristic | Filter only, never a trigger |
| Supertrend | Trend | Practitioner-derived (ATR-band trend flip), no academic validation surfaced; conceptually an ATR-scaled trend filter, similar mechanism to Keltner Channels | Usable as trend-direction filter; correlated with ATR-based Keltner — pick one per strategy |
| Ichimoku | Trend | No rigorous out-of-sample study surfaced; a bundle of several moving averages — high redundancy with EMA/SMA-based trend measures | Not used this pass (redundant, adds parameter surface) |
| Donchian channels | Trend/Volatility | Backing: Turtle-system trend following, Moskowitz et al.-style persistence; low win rate/high R:R as noted in §2.1 | Used as breakout trigger in Family 2 |
| Linear regression slope | Trend | Direct trend-strength proxy, mathematically related to momentum; no distinct evidence found beyond general momentum literature | Not used this pass (redundant with EMA slope/ADX) |
| RSI | Momentum | Academic review: *"RSI... did not exhibit a clear advantage in out-of-sample prediction or final returns"* vs. raw price features; *"technical rules... are not persistent... perform significantly worse than buy-and-hold"* out-of-sample in later periods | Used only as a **pullback-depth trigger inside an already-filtered trend**, never as a standalone overbought/oversold system |
| Stochastic / StochRSI | Momentum | Same family as RSI (bounded oscillator of price/RSI); highly correlated with RSI | Redundant with RSI — not used standalone |
| CCI | Momentum | Same oscillator family, mean-reversion-around-typical-price; not independently validated, correlated with RSI/Stochastic | Not used this pass (redundancy) |
| Williams %R | Momentum | Mathematically a rescaled Stochastic; fully redundant | Not used |
| ROC | Momentum | Simple momentum proxy, correlated with EMA-slope trend measures | Not used this pass (redundant with trend filter) |
| Bollinger Bands (+BW/%B) | Volatility | Widely used for mean-reversion entries; practitioner claims (e.g. "82% of band touches preceded reversals," "76% of squeezes led to 8%+ moves") are **unsourced marketing figures**, not verified — treated as folklore, not evidence | Used as breakout/squeeze trigger (Family 2), not as an unfiltered reversion signal |
| ATR | Volatility | No independent "edge" claimed by ATR itself — used universally in the risk-management literature (this brief's own hard rule requires cost/slippage modelling; ATR-based stops are the standard way to scale stop distance to current volatility) | Used in all 3 families for stop/target sizing |
| Keltner Channels | Volatility | ATR-band construction, conceptually redundant with Supertrend/Bollinger depending on multiplier | Pick one ATR-band tool per strategy to avoid redundancy |
| Historical volatility | Volatility | Used for regime classification (high/low vol regime), similar role to ADX but price-based rather than directional-movement-based | Considered but ADX chosen as the regime filter to avoid double-counting with ATR-based stops |
| VWAP | Volume | Execution-benchmark tool more than a predictive signal at 1h/4h swing timeframes (more relevant intraday/HFT) | Not used this pass |
| OBV | Volume | Cumulative volume-flow proxy; used qualitatively as confirmation, no independent out-of-sample validation surfaced | Optional confirmation leg in Family 2 |
| MFI | Volume | "Volume-weighted RSI" — correlated with both RSI and OBV | Not used (redundant) |
| CMF | Volume | Similar construction to OBV/MFI (accumulation/distribution family) | Not used (redundant with OBV) |
| Pivot points / swing hi-lo / fib retracement / prior-day/week hi-lo / round numbers | Structure | Practitioner consensus: value comes from **where stops and resting orders cluster**, not from any inherent predictive formula — i.e. these are self-fulfilling via crowd behavior, not a modelled edge | Documented/implemented but not used as a signal in the 3 chosen strategies this pass (adds parameter surface without a clear mechanism fit for the chosen families); available for future stop-placement refinement |
| Candlestick patterns (engulfing, hammer/shooting star, doji, inside bar) | Pattern | Long-running academic debate; most rigorous studies find weak/no standalone edge once transaction costs are included, similar to the broader technical-indicator literature findings above | Implemented and tested per Phase 2b requirement, not included as a signal leg in the 3 chosen strategies (kept out of the parameter budget) |
| Funding rate / OI / long-short ratio / basis / netflow | Crypto-specific | See §2.4 — real, documented edge (funding carry) but requires perp-futures/on-chain data this pass doesn't fetch | Stubbed, documented unavailable this pass |

**Redundancy takeaway**: momentum oscillators (RSI/Stoch/StochRSI/CCI/Williams
%R/ROC) are highly correlated with each other (same underlying
price-velocity information); volume-flow indicators (OBV/MFI/CMF) are
similarly correlated; ATR-band tools (ATR/Keltner/Supertrend) are correlated
by construction. The 3 chosen strategies each draw **at most one** indicator
from each of these three correlated clusters, consistent with the brief's
"drop signals correlating above 0.8" rule — verified quantitatively in Phase
4 via the correlation-matrix step, not just asserted here.

---

## 4. Top 3 families selected for implementation

Given §1's tension and the evidence above, the three families implemented in
`bot/strategies/` are all **trend-filtered, defined-R:R hybrids** — none is a
naive single-indicator system:

1. **Trend-filtered mean-reversion pullback** (`trend_filtered_pullback.py`,
   primary pick). Long entries only when a higher-timeframe trend filter
   (EMA200 + ADX>threshold) confirms an uptrend already in force, triggered
   by an RSI pullback (not an unfiltered oversold fade), with ATR-scaled
   stop/target. *Why this plausibly clears win rate ≥55% and PF ≥1.3
   together*: it inherits mean-reversion's higher hit rate (§2.2) but
   discards mean-reversion's most dangerous failure mode (fading a real
   trend reversal) by requiring the trend filter to agree first — the
   trade thesis is "buy temporary weakness in a confirmed uptrend," not
   "buy any oversold reading."

2. **Volatility-regime breakout with trend confirmation**
   (`volatility_breakout_trend.py`). Bollinger-squeeze/Donchian breakout
   taken only in the direction of a trend filter (Supertrend), ATR
   stop with a partial-profit-then-trail exit. *Why this is worth testing
   despite breakout systems' typical low win rate (§2.1)*: the trend filter
   should cut the false-breakout rate that drives breakout systems' low win
   rate, and the partial-profit/trail exit converts some of the "big winner,
   many small losers" shape toward a more moderate, more consistent R:R —
   this is the family most likely to fail the win-rate gate even after
   filtering, and is the first candidate for the escape hatch if it does.

3. **Trend-continuation confluence**
   (`trend_continuation_confluence.py`). EMA/MACD-cross-established
   direction (note: MACD used here for its histogram-momentum property, not
   stacked with EMA cross redundantly — direction comes from EMA, timing
   confirmation from MACD histogram slope), entry gated by a shallow RSI
   pullback *within* the trend (never counter-trend), ATR stop/target. This
   sits between families 1 and 2 — closer to "textbook trend-following" than
   Family 1, but with the RSI-pullback gate specifically added to avoid
   chasing breakouts at poor R:R (the documented weakness of pure breakout
   entries).

All three keep to **≤4 indicators drawn from different categories** (Trend +
Momentum + Volatility, optionally + Volume), consistent with §3's redundancy
findings, and every indicator's docstring states its mechanism per the
brief's "no popularity-only rationale" rule.

**Expectation going in**: Family 1 is judged the most likely to have a shot
at clearing every Definition-of-Done gate simultaneously; Families 2 and 3
are included because the brief calls for 3 families and because their
hybridization still has a plausible (if less certain) mechanism — but per
§1, it would not be surprising if **none** clear every gate on a 2-pair,
2-timeframe, 3-year dataset with only 200+ trades required and thin
walk-forward window counts on 4h. That outcome is FINDINGS.md, not failure.

---

## Sources consulted

- Moskowitz, Ooi & Pedersen (2012), *Time Series Momentum*, Journal of
  Financial Economics — https://w4.stern.nyu.edu/facdir/lpederse/papers/TimeSeriesMomentum.pdf
- López de Prado (2018), *Advances in Financial Machine Learning* (triple-barrier method) — summarized via https://quantstrategy.io/blog/the-triple-barrier-method-revolutionizing-how-we-label/ and https://reasonabledeviations.com/notes/adv_fin_ml/
- Enhanced Genetic-Algorithm-Driven Triple Barrier Labeling for crypto pair trading, *Mathematics* (MDPI, 2024) — https://www.mdpi.com/2227-7390/12/5/780
- Chan, S. (2025), *Leveraged BTC Funding Carry Algorithm*, SSRN — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5292305
- Technical-indicator out-of-sample evidence: https://arxiv.org/html/2412.15448v1 ; https://link.springer.com/article/10.1007/s11408-023-00433-2 ; https://harbourfrontquant.substack.com/p/the-limits-of-out-of-sample-testing
- Order flow imbalance / crypto microstructure: https://aligrithm.com/order-book-imbalance-the-first-microstructure-feature-to-test/ ; https://www.frontiersin.org/journals/blockchain/articles/10.3389/fbloc.2026.1811716/full
- Bitcoin time-of-day/day-of-week effects: https://mlquants.substack.com/p/are-day-of-the-week-effects-in-cryptocurrencies ; https://quantpedia.com/strategies/intraday-seasonality-in-bitcoin
- ADX as regime filter [practitioner]: https://hoclamtrader.com/en/adx-trend-strength-filter-trades/
- Donchian/turtle breakout backtests [practitioner]: https://www.altrady.com/blog/crypto-trading-strategies/donchian-channel-strategy ; https://www.academia.edu/68475740/Testing_a_price_breakout_strategy_using_Donchian_Channels
- Bollinger/RSI mean reversion [practitioner, figures unverified]: https://medium.com/@redsword_23261/enhanced-mean-reversion-strategy-with-bollinger-bands-and-rsi-integration-87ec8ca1059f
