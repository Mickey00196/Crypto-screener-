import type { Coin, SetupFilter } from './types';

/**
 * Lightweight, screener-wide setup tag derived only from data already present
 * in the markets payload (7d sparkline + change %s) — cheap enough to run
 * across hundreds of rows client-side. This is a coarse filter, not the full
 * confluence analysis; the coin detail page runs the real indicator engine
 * against daily OHLC for an honest, per-signal breakdown.
 */
export function quickSetupTag(coin: Coin): Exclude<SetupFilter, 'any'> | null {
  const series = coin.sparkline_in_7d?.price;
  const change24h = coin.price_change_percentage_24h_in_currency ?? 0;
  const change7d = coin.price_change_percentage_7d_in_currency ?? 0;

  if (!series || series.length < 20) return null;

  const recentWindow = series.slice(-24); // ~last 24h of hourly points
  const priorWindow = series.slice(-72, -24);
  const recentHigh = Math.max(...recentWindow);
  const priorHigh = priorWindow.length ? Math.max(...priorWindow) : recentHigh;
  const last = series[series.length - 1]!;
  const first = series[0]!;

  const brokeOut = last >= recentHigh * 0.995 && recentHigh > priorHigh;
  const nearAth7d = last >= Math.max(...series) * 0.98;
  const nearAtl7d = last <= Math.min(...series) * 1.02;

  if (brokeOut && change24h > 2) return 'breakout';
  if (change24h > 0 && change7d > 0 && last > first) {
    if (nearAth7d) return 'resistance-retest';
    return 'bullish';
  }
  if (change24h < 0 && change7d < 0 && last < first) return 'bearish';
  if (nearAtl7d) return 'resistance-retest';

  return null;
}

export function matchesSetupFilter(coin: Coin, filter: SetupFilter): boolean {
  if (filter === 'any') return true;
  const tag = quickSetupTag(coin);
  if (filter === 'bullish') return tag === 'bullish' || tag === 'breakout';
  if (filter === 'bearish') return tag === 'bearish';
  if (filter === 'breakout') return tag === 'breakout';
  if (filter === 'resistance-retest') return tag === 'resistance-retest';
  if (filter === 'golden-cross') return false; // requires daily OHLC — evaluated on detail page only
  return true;
}
