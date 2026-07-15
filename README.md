# Pulse — Crypto Screener

A real-time crypto screener built for density without clutter: filter thousands of tokens, screen for technical setups, and browse a live market heatmap — all in a dark, terminal-grade UI designed to feel like it belongs in a funded trading desk, not a spreadsheet.

Built from [the project spec](./SPEC.md) as a fast-shipping MVP + v2 slice: market/technical filters, saved screens, watchlists, a visual heatmap mode, and an experimental technical-setup detector — all running on a single Next.js app with no backend infrastructure to stand up.

## Stack

| Layer | Choice |
|---|---|
| Framework | Next.js 15 (App Router) + TypeScript |
| Styling | Tailwind CSS, custom dark design system (no component kit dependency beyond Radix primitives) |
| Data fetching | TanStack Query, 45s polling refresh |
| Charts | TradingView's `lightweight-charts`, hand-rolled SVG sparklines, a squarified treemap for the heatmap |
| Market data | CoinGecko public API, proxied through Next API routes with server-side caching |
| Persistence | Browser `localStorage` for watchlist + saved screens — no account system for v1 |

No database, Redis, or separate backend service. This is a deliberate scope call for a fast, deployable MVP: CoinGecko's markets endpoint plus Next's server-side fetch cache is enough to serve a screener against ~500 coins with a ~45s effective refresh, and `localStorage` covers watchlists/presets without needing auth. See **Scaling up** below for the path to the fuller architecture in the original spec (Postgres, Redis, accounts) once this needs to support real concurrent users or on-chain/derivatives data.

## Features shipped

**Screener**
- Filters: market cap, price, 24h/7d % change, volume, circulating/total supply ratio, and a "setup" filter (bullish/bearish/breakout/key-level-retest)
- Sortable, column-customizable results table; responsive — collapses to a card list on mobile
- Quick-filter chips + an advanced filter panel; debounced search-as-you-type
- Save/load custom screens (and 6 built-in presets: top gainers/losers, high volume, large cap, small-cap momentum, bullish setups) — persisted to `localStorage`
- Live-ish refresh every 45s via TanStack Query, with a sync indicator in the header

**Visual screener mode**
- Market heatmap (squarified treemap): tile size = market cap, color = 24h change, click-through to coin detail

**Coin detail**
- Price chart (24h/7d/30d/90d/1y/max) via TradingView's lightweight-charts
- Key stats: market cap, FDV, volume, supply figures, ATH/ATL
- Watchlist toggle, external links (homepage, explorers, social)

**Technical Analysis Setup Detector** (experimental)
- Computes SMA20/50/200, RSI14, OBV, and structural signals (breakouts, golden/death cross, higher-highs/higher-lows, volume spikes) from daily OHLC
- Combines signals into a confluence score and a Low/Medium/High confidence tier — never fires on a single indicator alone
- **Backtests against the coin's own price history**: when a signal fires, it looks back at every prior occurrence of that same signal for that asset and reports the actual forward win-rate, average move, and sample size — a real (if small-n) statistic, not a fabricated global number
- UI copy is deliberately hedged ("historically," win-rate + sample size shown, "not financial advice") per the spec's honesty requirement — this is pattern-matching against history, not a prediction

**Watchlist**
- Star any coin from anywhere in the app; persisted locally, no account needed

## Design principles followed

Dark-mode-only by default, monospace tabular figures for all numbers, one consistent green/red pair for gains/losses (no rainbow dashboards), debounced client-side filtering for near-instant perceived response, and empty states everywhere a list could otherwise render blank.

## Getting started

```bash
npm install
npm run dev
```

Open http://localhost:3000. No API key or environment variables required — CoinGecko's public tier is used as-is (see **Known limitations**).

```bash
npm run build   # production build
npm run lint    # eslint
```

## Project structure

```
app/                    Routes (App Router) + API proxy routes
  api/coins/             Markets list, coin detail, chart/OHLC, search — all proxy CoinGecko with server-side caching
  coin/[id]/             Coin detail page
  heatmap/, watchlist/   Secondary views
components/
  screener/               Filter bar, results table, presets, column picker, heatmap
  coin/                   Price chart, stats grid, setup detector, explorer links
  layout/, shared/, ui/   Header/nav, sparkline/price-change/empty-state, design-system primitives
lib/
  coingecko.ts            CoinGecko client
  indicators.ts            SMA/RSI/OBV + setup detection + self-backtest
  filterCoins.ts, quickSetup.ts, treemap.ts, presets.ts, storage.ts, columns.ts
```

## Known limitations

- **CoinGecko free tier**: no API key, rate-limited, ~500 coins covered (2 pages of the markets endpoint). Swapping in CoinMarketCap Pro/CryptoCompare or an API key just means changing `lib/coingecko.ts`.
- **45s polling, not websockets**: matches the spec's MVP scope ("30-60s polling is fine for MVP, websockets later").
- **No accounts**: watchlists and saved screens live in browser `localStorage`. Fine for a personal tool or a fast public launch; adding Clerk/Supabase Auth + Postgres is the natural v2 step once cross-device sync matters.
- **Setup Detector is per-asset, not cross-market**: the spec's vision includes a nightly batch job backtesting thousands of historical setups across the whole market to build a global lookup table. That needs real infrastructure (a scheduled job + a datastore) that doesn't make sense to stand up for an MVP. What's shipped instead is honest and real: each coin's own history is backtested live, in-browser data, with the sample size always shown. The next step toward the full spec is a scheduled job (Vercel Cron / a small worker) that runs the same `lib/indicators.ts` logic across the tracked universe and writes results to a database.
- **On-chain data (holder count, liquidity depth, contract risk) is out of scope for this pass** — it's a v2/v3 item in the spec and needs a provider like Covalent/Moralis plus its own data model for multi-chain tokens.

## Scaling up (from the original spec's architecture)

This ships as a single Next.js app on purpose. When it needs to scale past a personal/demo tool:

1. **Add Postgres** for saved screens/watchlists/alerts once accounts exist, and to store the pre-computed setup-detector backtest table instead of computing it live.
2. **Add Redis** as a hot price cache in front of the market-data provider once traffic outgrows what Next's fetch cache comfortably absorbs.
3. **Move indicator computation to a scheduled job** (nightly/intraday) rather than computing on page load, per the spec's "Implementation approach" — this is what unlocks screening *for* setups across the whole universe cheaply, and cross-market backtest stats instead of per-asset ones.
4. **Auth** via Clerk or Supabase once watchlists need to follow a user across devices.

## A note on the Technical Analysis Setup Detector

This is a statistical pattern-matching tool, not financial advice and not a guarantee. Every setup shown includes the sample size and historical win-rate it's based on, and low-volume or newly-listed tokens will have thin sample sizes — treat the numbers as directional context, not precise probabilities.
