'use client';

import { useMemo, useState } from 'react';
import { Bookmark } from 'lucide-react';
import { useCoins } from '@/lib/hooks/useCoins';
import { useWatchlist } from '@/lib/hooks/useWatchlist';
import { DEFAULT_COLUMNS } from '@/lib/columns';
import { sortCoins } from '@/lib/filterCoins';
import type { ColumnConfig, SortDirection, SortKey } from '@/lib/types';
import { ResultsTable } from '@/components/screener/ResultsTable';
import { EmptyState } from '@/components/shared/EmptyState';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';

export default function WatchlistPage() {
  const { data: coins, isLoading } = useCoins();
  const { ids, isWatched, toggle, ready } = useWatchlist();
  const [columns] = useState<ColumnConfig[]>(DEFAULT_COLUMNS);
  const [sortKey, setSortKey] = useState<SortKey>('market_cap_rank');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const watched = useMemo(() => {
    if (!coins) return [];
    const set = new Set(ids);
    return sortCoins(
      coins.filter((c) => set.has(c.id)),
      sortKey,
      sortDirection
    );
  }, [coins, ids, sortKey, sortDirection]);

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
    else {
      setSortKey(key);
      setSortDirection('desc');
    }
  }

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col gap-4 px-4 py-5 md:px-6 md:py-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight text-base-50">Watchlist</h1>
        <p className="text-sm text-neutral">Saved to this browser. {ids.length} token{ids.length === 1 ? '' : 's'} tracked.</p>
      </div>

      {ready && ids.length === 0 ? (
        <EmptyState
          icon={Bookmark}
          title="Your watchlist is empty"
          description="Star any coin from the screener to track it here. It's saved locally in this browser — no account needed."
          action={
            <Link href="/">
              <Button variant="accent" size="sm">
                Browse screener
              </Button>
            </Link>
          }
        />
      ) : (
        <ResultsTable
          coins={watched}
          loading={isLoading || !ready}
          columns={columns}
          sortKey={sortKey}
          sortDirection={sortDirection}
          onSort={handleSort}
          isWatched={isWatched}
          onToggleWatch={toggle}
        />
      )}
    </div>
  );
}
