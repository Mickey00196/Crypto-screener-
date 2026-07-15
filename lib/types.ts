export interface Coin {
  id: string;
  symbol: string;
  name: string;
  image: string;
  current_price: number;
  market_cap: number;
  market_cap_rank: number | null;
  fully_diluted_valuation: number | null;
  total_volume: number;
  high_24h: number | null;
  low_24h: number | null;
  price_change_percentage_24h: number | null;
  price_change_percentage_1h_in_currency?: number | null;
  price_change_percentage_24h_in_currency?: number | null;
  price_change_percentage_7d_in_currency?: number | null;
  price_change_percentage_30d_in_currency?: number | null;
  circulating_supply: number;
  total_supply: number | null;
  max_supply: number | null;
  ath: number;
  ath_change_percentage: number;
  atl: number;
  atl_change_percentage: number;
  sparkline_in_7d?: { price: number[] };
  last_updated: string;
}

export interface FilterState {
  search: string;
  marketCapMin: number | null;
  marketCapMax: number | null;
  volumeMin: number | null;
  change24hMin: number | null;
  change24hMax: number | null;
  change7dMin: number | null;
  change7dMax: number | null;
  priceMin: number | null;
  priceMax: number | null;
  supplyRatioMax: number | null; // circulating / total
  setup: SetupFilter;
}

export type SetupFilter = 'any' | 'bullish' | 'bearish' | 'breakout' | 'resistance-retest' | 'golden-cross';

export type SortKey =
  | 'market_cap_rank'
  | 'name'
  | 'current_price'
  | 'price_change_percentage_1h_in_currency'
  | 'price_change_percentage_24h_in_currency'
  | 'price_change_percentage_7d_in_currency'
  | 'total_volume'
  | 'market_cap';

export type SortDirection = 'asc' | 'desc';

export interface ScreenPreset {
  id: string;
  name: string;
  builtIn?: boolean;
  filters: FilterState;
  sortKey: SortKey;
  sortDirection: SortDirection;
  createdAt: number;
}

export interface ColumnConfig {
  key: SortKey | 'sparkline' | 'watchlist' | 'setup';
  label: string;
  visible: boolean;
}

export type ConfidenceTier = 'Low' | 'Medium' | 'High';

export interface SignalResult {
  key: string;
  label: string;
  fired: boolean;
  detail: string;
}

export interface SetupResult {
  label: string;
  bias: 'bullish' | 'bearish' | 'neutral';
  confidence: ConfidenceTier;
  score: number;
  winRate: number | null;
  avgMove: number | null;
  sampleSize: number | null;
  signals: SignalResult[];
  summary: string;
}

export interface MarketChartPoint {
  time: number;
  value: number;
}
