import type { Coin } from './types';

const BASE_URL = 'https://api.coingecko.com/api/v3';

// CoinGecko's free tier rate-limits aggressively. We fetch server-side and let
// Next's fetch cache absorb repeat requests instead of hitting the API per client.
const REVALIDATE_SECONDS = 45;

async function cgFetch<T>(path: string, params: Record<string, string | number | boolean | undefined> = {}): Promise<T> {
  const url = new URL(`${BASE_URL}${path}`);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) url.searchParams.set(key, String(value));
  }

  const res = await fetch(url.toString(), {
    headers: { Accept: 'application/json' },
    next: { revalidate: REVALIDATE_SECONDS },
  });

  if (!res.ok) {
    throw new Error(`CoinGecko request failed (${res.status}): ${path}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchMarkets(opts: { page?: number; perPage?: number; ids?: string[] } = {}): Promise<Coin[]> {
  return cgFetch<Coin[]>('/coins/markets', {
    vs_currency: 'usd',
    order: 'market_cap_desc',
    per_page: opts.perPage ?? 250,
    page: opts.page ?? 1,
    sparkline: true,
    price_change_percentage: '1h,24h,7d,30d',
    ids: opts.ids?.join(','),
  });
}

export async function fetchCoinDetail(id: string) {
  return cgFetch<any>(`/coins/${id}`, {
    localization: false,
    tickers: false,
    market_data: true,
    community_data: false,
    developer_data: false,
    sparkline: true,
  });
}

export async function fetchMarketChart(id: string, days: number | 'max' = 200): Promise<{ prices: [number, number][]; total_volumes: [number, number][] }> {
  return cgFetch<any>(`/coins/${id}/market_chart`, {
    vs_currency: 'usd',
    days,
  });
}

export async function fetchOHLC(id: string, days: number = 90): Promise<[number, number, number, number, number][]> {
  return cgFetch<any>(`/coins/${id}/ohlc`, {
    vs_currency: 'usd',
    days,
  });
}

export async function searchCoins(query: string) {
  return cgFetch<{ coins: Array<{ id: string; name: string; symbol: string; market_cap_rank: number | null; thumb: string }> }>('/search', {
    query,
  });
}
