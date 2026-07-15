'use client';

import { useMemo, useState } from 'react';
import { useCoins } from '@/lib/hooks/useCoins';
import { HeatmapView } from '@/components/screener/HeatmapView';
import { formatNumber } from '@/lib/format';
import { cn } from '@/lib/utils';

const SCOPES = [
  { label: 'Top 100', value: 100 },
  { label: 'Top 250', value: 250 },
  { label: 'Top 500', value: 500 },
];

export default function HeatmapPage() {
  const { data: coins, isLoading } = useCoins();
  const [scope, setScope] = useState(100);

  const scoped = useMemo(() => (coins ?? []).slice(0, scope), [coins, scope]);

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col gap-4 px-4 py-5 md:px-6 md:py-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight text-base-50">Market Heatmap</h1>
        <p className="text-sm text-neutral">
          Tile size = market cap, color = 24h change. {coins ? `${formatNumber(scoped.length)} tokens shown` : 'Loading…'}
        </p>
      </div>

      <div className="flex items-center gap-1.5">
        {SCOPES.map((s) => (
          <button
            key={s.value}
            onClick={() => setScope(s.value)}
            className={cn(
              'focus-ring rounded-full border px-3 py-1.5 text-xs font-medium transition-colors',
              scope === s.value ? 'border-accent/50 bg-accent/10 text-accent-glow' : 'border-base-border bg-base-raised text-neutral hover:text-base-50'
            )}
          >
            {s.label}
          </button>
        ))}
      </div>

      <HeatmapView coins={scoped} loading={isLoading} />
    </div>
  );
}
