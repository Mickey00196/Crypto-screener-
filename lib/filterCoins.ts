import type { Coin, FilterState, SortDirection, SortKey } from './types';
import { matchesSetupFilter } from './quickSetup';

export function filterCoins(coins: Coin[], filters: FilterState): Coin[] {
  const search = filters.search.trim().toLowerCase();

  return coins.filter((coin) => {
    if (search && !coin.name.toLowerCase().includes(search) && !coin.symbol.toLowerCase().includes(search)) {
      return false;
    }
    if (filters.marketCapMin !== null && (coin.market_cap ?? 0) < filters.marketCapMin) return false;
    if (filters.marketCapMax !== null && (coin.market_cap ?? 0) > filters.marketCapMax) return false;
    if (filters.volumeMin !== null && (coin.total_volume ?? 0) < filters.volumeMin) return false;
    if (filters.priceMin !== null && (coin.current_price ?? 0) < filters.priceMin) return false;
    if (filters.priceMax !== null && (coin.current_price ?? 0) > filters.priceMax) return false;

    const change24h = coin.price_change_percentage_24h_in_currency ?? coin.price_change_percentage_24h;
    if (filters.change24hMin !== null && (change24h ?? -Infinity) < filters.change24hMin) return false;
    if (filters.change24hMax !== null && (change24h ?? Infinity) > filters.change24hMax) return false;

    const change7d = coin.price_change_percentage_7d_in_currency;
    if (filters.change7dMin !== null && (change7d ?? -Infinity) < filters.change7dMin) return false;
    if (filters.change7dMax !== null && (change7d ?? Infinity) > filters.change7dMax) return false;

    if (filters.supplyRatioMax !== null && coin.total_supply) {
      const ratio = coin.circulating_supply / coin.total_supply;
      if (ratio > filters.supplyRatioMax) return false;
    }

    if (!matchesSetupFilter(coin, filters.setup)) return false;

    return true;
  });
}

export function sortCoins(coins: Coin[], key: SortKey, direction: SortDirection): Coin[] {
  const sorted = [...coins].sort((a, b) => {
    let av: number | string | null;
    let bv: number | string | null;

    if (key === 'name') {
      av = a.name;
      bv = b.name;
    } else if (key === 'market_cap_rank') {
      av = a.market_cap_rank ?? Infinity;
      bv = b.market_cap_rank ?? Infinity;
    } else {
      av = (a[key] as number | null) ?? -Infinity;
      bv = (b[key] as number | null) ?? -Infinity;
    }

    if (typeof av === 'string' || typeof bv === 'string') {
      const cmp = String(av).localeCompare(String(bv));
      return direction === 'asc' ? cmp : -cmp;
    }
    const cmp = (av as number) - (bv as number);
    return direction === 'asc' ? cmp : -cmp;
  });
  return sorted;
}
