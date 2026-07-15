'use client';

import { SlidersHorizontal, X } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import type { FilterState, SetupFilter } from '@/lib/types';
import { EMPTY_FILTERS } from '@/lib/presets';
import { cn } from '@/lib/utils';

const SETUP_OPTIONS: { value: SetupFilter; label: string }[] = [
  { value: 'any', label: 'Any setup' },
  { value: 'bullish', label: 'Bullish' },
  { value: 'bearish', label: 'Bearish' },
  { value: 'breakout', label: 'Breakout' },
  { value: 'resistance-retest', label: 'Key level retest' },
];

const QUICK_RANGES: { label: string; patch: Partial<FilterState> }[] = [
  { label: 'Market cap > $1B', patch: { marketCapMin: 1_000_000_000 } },
  { label: 'Market cap < $100M', patch: { marketCapMax: 100_000_000 } },
  { label: 'Volume > $50M', patch: { volumeMin: 50_000_000 } },
  { label: '24h gainers', patch: { change24hMin: 0 } },
  { label: '24h losers', patch: { change24hMax: 0 } },
];

function isActive(filters: FilterState, patch: Partial<FilterState>) {
  return Object.entries(patch).every(([k, v]) => filters[k as keyof FilterState] === v);
}

function countActiveFilters(filters: FilterState): number {
  let n = 0;
  if (filters.marketCapMin !== null) n++;
  if (filters.marketCapMax !== null) n++;
  if (filters.volumeMin !== null) n++;
  if (filters.change24hMin !== null) n++;
  if (filters.change24hMax !== null) n++;
  if (filters.change7dMin !== null) n++;
  if (filters.change7dMax !== null) n++;
  if (filters.priceMin !== null) n++;
  if (filters.priceMax !== null) n++;
  if (filters.supplyRatioMax !== null) n++;
  if (filters.setup !== 'any') n++;
  return n;
}

export function FilterBar({
  filters,
  onChange,
}: {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
}) {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const activeCount = countActiveFilters(filters);

  function patch(p: Partial<FilterState>) {
    onChange({ ...filters, ...p });
  }

  function toggleQuick(p: Partial<FilterState>) {
    if (isActive(filters, p)) {
      const reset: Partial<FilterState> = {};
      for (const key of Object.keys(p)) reset[key as keyof FilterState] = null as never;
      patch(reset);
    } else {
      patch(p);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex flex-wrap gap-1.5 no-scrollbar">
          {QUICK_RANGES.map((q) => (
            <button
              key={q.label}
              onClick={() => toggleQuick(q.patch)}
              className={cn(
                'focus-ring whitespace-nowrap rounded-full border px-3 py-1.5 text-xs font-medium transition-colors',
                isActive(filters, q.patch)
                  ? 'border-accent/50 bg-accent/10 text-accent-glow'
                  : 'border-base-border bg-base-raised text-neutral hover:text-base-50'
              )}
            >
              {q.label}
            </button>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2">
          <select
            value={filters.setup}
            onChange={(e) => patch({ setup: e.target.value as SetupFilter })}
            className="focus-ring h-8 rounded-full border border-base-border bg-base-raised px-3 text-xs font-medium text-base-50"
          >
            {SETUP_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          <Button size="sm" variant="outline" onClick={() => setAdvancedOpen((v) => !v)} className="relative">
            <SlidersHorizontal size={13} />
            Filters
            {activeCount > 0 && (
              <span className="absolute -right-1.5 -top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-accent text-[10px] text-white">
                {activeCount}
              </span>
            )}
          </Button>

          {activeCount > 0 && (
            <Button size="sm" variant="ghost" onClick={() => onChange({ ...EMPTY_FILTERS, search: filters.search })}>
              <X size={13} />
              Clear
            </Button>
          )}
        </div>
      </div>

      {advancedOpen && (
        <div className="grid animate-slide-up grid-cols-2 gap-3 rounded-xl2 border border-base-border bg-base-surface p-4 sm:grid-cols-3 lg:grid-cols-6">
          <FilterField label="Min market cap">
            <Input
              type="number"
              placeholder="$0"
              value={filters.marketCapMin ?? ''}
              onChange={(e) => patch({ marketCapMin: e.target.value ? Number(e.target.value) : null })}
            />
          </FilterField>
          <FilterField label="Max market cap">
            <Input
              type="number"
              placeholder="No limit"
              value={filters.marketCapMax ?? ''}
              onChange={(e) => patch({ marketCapMax: e.target.value ? Number(e.target.value) : null })}
            />
          </FilterField>
          <FilterField label="Min 24h volume">
            <Input
              type="number"
              placeholder="$0"
              value={filters.volumeMin ?? ''}
              onChange={(e) => patch({ volumeMin: e.target.value ? Number(e.target.value) : null })}
            />
          </FilterField>
          <FilterField label="Min price">
            <Input
              type="number"
              placeholder="$0"
              value={filters.priceMin ?? ''}
              onChange={(e) => patch({ priceMin: e.target.value ? Number(e.target.value) : null })}
            />
          </FilterField>
          <FilterField label="Max price">
            <Input
              type="number"
              placeholder="No limit"
              value={filters.priceMax ?? ''}
              onChange={(e) => patch({ priceMax: e.target.value ? Number(e.target.value) : null })}
            />
          </FilterField>
          <FilterField label="24h change %">
            <div className="flex items-center gap-1.5">
              <Input
                type="number"
                placeholder="Min"
                value={filters.change24hMin ?? ''}
                onChange={(e) => patch({ change24hMin: e.target.value ? Number(e.target.value) : null })}
              />
              <Input
                type="number"
                placeholder="Max"
                value={filters.change24hMax ?? ''}
                onChange={(e) => patch({ change24hMax: e.target.value ? Number(e.target.value) : null })}
              />
            </div>
          </FilterField>
          <FilterField label="7d change %">
            <div className="flex items-center gap-1.5">
              <Input
                type="number"
                placeholder="Min"
                value={filters.change7dMin ?? ''}
                onChange={(e) => patch({ change7dMin: e.target.value ? Number(e.target.value) : null })}
              />
              <Input
                type="number"
                placeholder="Max"
                value={filters.change7dMax ?? ''}
                onChange={(e) => patch({ change7dMax: e.target.value ? Number(e.target.value) : null })}
              />
            </div>
          </FilterField>
          <FilterField label="Max circ./total supply">
            <Input
              type="number"
              step="0.05"
              placeholder="e.g. 0.5"
              value={filters.supplyRatioMax ?? ''}
              onChange={(e) => patch({ supplyRatioMax: e.target.value ? Number(e.target.value) : null })}
            />
          </FilterField>
        </div>
      )}
    </div>
  );
}

function FilterField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[11px] font-medium uppercase tracking-wide text-neutral">{label}</span>
      {children}
    </label>
  );
}
