'use client';

import { useMemo, useState } from 'react';
import { AlertTriangle, Search } from 'lucide-react';
import { useCoins } from '@/lib/hooks/useCoins';
import { useWatchlist } from '@/lib/hooks/useWatchlist';
import { usePresets } from '@/lib/hooks/usePresets';
import { useDebounce } from '@/lib/hooks/useDebounce';
import { EMPTY_FILTERS } from '@/lib/presets';
import { DEFAULT_COLUMNS } from '@/lib/columns';
import { filterCoins, sortCoins } from '@/lib/filterCoins';
import type { ColumnConfig, FilterState, ScreenPreset, SortDirection, SortKey } from '@/lib/types';
import { FilterBar } from '@/components/screener/FilterBar';
import { PresetBar } from '@/components/screener/PresetBar';
import { ColumnCustomizer } from '@/components/screener/ColumnCustomizer';
import { ResultsTable } from '@/components/screener/ResultsTable';
import { Input } from '@/components/ui/Input';
import { formatNumber } from '@/lib/format';

export default function ScreenerPage() {
  const { data: coins, isLoading, isError } = useCoins();
  const { isWatched, toggle } = useWatchlist();
  const { presets, save, remove } = usePresets();

  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS);
  const [searchInput, setSearchInput] = useState('');
  const debouncedSearch = useDebounce(searchInput, 150);
  const [sortKey, setSortKey] = useState<SortKey>('market_cap_rank');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [columns, setColumns] = useState<ColumnConfig[]>(DEFAULT_COLUMNS);
  const [activePresetId, setActivePresetId] = useState<string | null>(null);

  const effectiveFilters = useMemo(() => ({ ...filters, search: debouncedSearch }), [filters, debouncedSearch]);

  const filtered = useMemo(() => {
    if (!coins) return [];
    return filterCoins(coins, effectiveFilters);
  }, [coins, effectiveFilters]);

  const sorted = useMemo(() => sortCoins(filtered, sortKey, sortDirection), [filtered, sortKey, sortDirection]);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDirection(key === 'name' ? 'asc' : 'desc');
    }
    setActivePresetId(null);
  }

  function handleFiltersChange(next: FilterState) {
    setFilters(next);
    setActivePresetId(null);
  }

  function applyPreset(preset: ScreenPreset) {
    setFilters(preset.filters);
    setSortKey(preset.sortKey);
    setSortDirection(preset.sortDirection);
    setActivePresetId(preset.id);
  }

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col gap-4 px-4 py-5 md:px-6 md:py-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight text-base-50">Screener</h1>
        <p className="text-sm text-neutral">
          {coins ? `${formatNumber(coins.length)} tokens tracked` : 'Loading market universe…'} · updates every 45s
        </p>
      </div>

      <PresetBar
        presets={presets}
        activePresetId={activePresetId}
        onSelect={applyPreset}
        onSave={save}
        onRemove={remove}
        currentFilters={filters}
        currentSort={sortKey}
        currentDirection={sortDirection}
      />

      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="relative w-full md:max-w-xs">
          <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-neutral" />
          <Input
            placeholder="Filter by name or symbol…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-8"
          />
        </div>
        <ColumnCustomizer columns={columns} onChange={setColumns} />
      </div>

      <FilterBar filters={filters} onChange={handleFiltersChange} />

      {isError && (
        <div className="flex items-center gap-2 rounded-lg border border-loss/30 bg-loss-bg px-4 py-3 text-sm text-loss">
          <AlertTriangle size={15} />
          Couldn&apos;t reach the market data provider. Retrying automatically — check back in a moment.
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-neutral">
        <span>{formatNumber(sorted.length)} results</span>
      </div>

      <ResultsTable
        coins={sorted}
        loading={isLoading}
        columns={columns}
        sortKey={sortKey}
        sortDirection={sortDirection}
        onSort={handleSort}
        isWatched={isWatched}
        onToggleWatch={toggle}
      />
    </div>
  );
}
