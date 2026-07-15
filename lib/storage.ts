import type { ScreenPreset } from './types';

const WATCHLIST_KEY = 'cs_watchlist_v1';
const PRESETS_KEY = 'cs_presets_v1';
const COLUMNS_KEY = 'cs_columns_v1';

function safeGet<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function safeSet<T>(key: string, value: T) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // storage full or unavailable — fail silently, non-critical feature
  }
}

export function getWatchlist(): string[] {
  return safeGet<string[]>(WATCHLIST_KEY, []);
}

export function setWatchlist(ids: string[]) {
  safeSet(WATCHLIST_KEY, ids);
}

export function getCustomPresets(): ScreenPreset[] {
  return safeGet<ScreenPreset[]>(PRESETS_KEY, []);
}

export function setCustomPresets(presets: ScreenPreset[]) {
  safeSet(PRESETS_KEY, presets);
}

export function getStoredColumns(): string[] | null {
  return safeGet<string[] | null>(COLUMNS_KEY, null);
}

export function setStoredColumns(cols: string[]) {
  safeSet(COLUMNS_KEY, cols);
}
