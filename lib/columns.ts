import type { ColumnConfig } from './types';

export const DEFAULT_COLUMNS: ColumnConfig[] = [
  { key: 'watchlist', label: '', visible: true },
  { key: 'market_cap_rank', label: '#', visible: true },
  { key: 'name', label: 'Name', visible: true },
  { key: 'current_price', label: 'Price', visible: true },
  { key: 'price_change_percentage_1h_in_currency', label: '1h', visible: true },
  { key: 'price_change_percentage_24h_in_currency', label: '24h', visible: true },
  { key: 'price_change_percentage_7d_in_currency', label: '7d', visible: true },
  { key: 'total_volume', label: '24h Volume', visible: true },
  { key: 'market_cap', label: 'Market Cap', visible: true },
  { key: 'setup', label: 'Setup', visible: true },
  { key: 'sparkline', label: '7d Chart', visible: true },
];

export const OPTIONAL_COLUMN_KEYS = new Set(['setup', 'sparkline', 'price_change_percentage_1h_in_currency']);
