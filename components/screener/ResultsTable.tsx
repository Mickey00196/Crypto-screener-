'use client';

import Image from 'next/image';
import Link from 'next/link';
import { ChevronDown, ChevronUp, Star } from 'lucide-react';
import type { Coin, ColumnConfig, SortDirection, SortKey } from '@/lib/types';
import { formatCompact, formatUsd } from '@/lib/format';
import { PriceChange } from '@/components/shared/PriceChange';
import { Sparkline } from '@/components/shared/Sparkline';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/shared/EmptyState';
import { SearchX } from 'lucide-react';
import { cn } from '@/lib/utils';
import { quickSetupTag } from '@/lib/quickSetup';

const SETUP_LABELS: Record<string, { label: string; tone: 'gain' | 'loss' | 'accent' }> = {
  bullish: { label: 'Bullish', tone: 'gain' },
  breakout: { label: 'Breakout', tone: 'gain' },
  bearish: { label: 'Bearish', tone: 'loss' },
  'resistance-retest': { label: 'Key level', tone: 'accent' },
};

function SetupBadge({ coin }: { coin: Coin }) {
  const tag = quickSetupTag(coin);
  if (!tag) return <span className="text-xs text-neutral/50">—</span>;
  const meta = SETUP_LABELS[tag];
  if (!meta) return null;
  const toneClass = meta.tone === 'gain' ? 'text-gain bg-gain-bg' : meta.tone === 'loss' ? 'text-loss bg-loss-bg' : 'text-accent-glow bg-accent/10';
  return <span className={cn('rounded-md px-2 py-0.5 text-[11px] font-medium', toneClass)}>{meta.label}</span>;
}

interface Props {
  coins: Coin[];
  loading: boolean;
  columns: ColumnConfig[];
  sortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
  isWatched: (id: string) => boolean;
  onToggleWatch: (id: string) => void;
}

export function ResultsTable({ coins, loading, columns, sortKey, sortDirection, onSort, isWatched, onToggleWatch }: Props) {
  const visible = (key: ColumnConfig['key']) => columns.find((c) => c.key === key)?.visible;

  if (loading) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 12 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (coins.length === 0) {
    return (
      <EmptyState
        icon={SearchX}
        title="No coins match these filters"
        description="Try widening your market cap or % change range, or clear filters to see the full universe."
      />
    );
  }

  return (
    <>
      {/* Desktop table */}
      <div className="hidden overflow-x-auto rounded-xl2 border border-base-border bg-base-surface md:block">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-base-border text-left text-xs text-neutral">
              <th className="w-9 px-3 py-3"></th>
              {visible('market_cap_rank') && <SortableHeader label="#" columnKey="market_cap_rank" activeKey={sortKey} sortDirection={sortDirection} onSort={onSort} className="w-12" />}
              <SortableHeader label="Name" columnKey="name" activeKey={sortKey} sortDirection={sortDirection} onSort={onSort} />
              {visible('current_price') && <SortableHeader label="Price" columnKey="current_price" activeKey={sortKey} sortDirection={sortDirection} onSort={onSort} align="right" />}
              {visible('price_change_percentage_1h_in_currency') && (
                <SortableHeader label="1h" columnKey="price_change_percentage_1h_in_currency" activeKey={sortKey} sortDirection={sortDirection} onSort={onSort} align="right" />
              )}
              {visible('price_change_percentage_24h_in_currency') && (
                <SortableHeader label="24h" columnKey="price_change_percentage_24h_in_currency" activeKey={sortKey} sortDirection={sortDirection} onSort={onSort} align="right" />
              )}
              {visible('price_change_percentage_7d_in_currency') && (
                <SortableHeader label="7d" columnKey="price_change_percentage_7d_in_currency" activeKey={sortKey} sortDirection={sortDirection} onSort={onSort} align="right" />
              )}
              {visible('total_volume') && <SortableHeader label="24h Volume" columnKey="total_volume" activeKey={sortKey} sortDirection={sortDirection} onSort={onSort} align="right" />}
              {visible('market_cap') && <SortableHeader label="Market Cap" columnKey="market_cap" activeKey={sortKey} sortDirection={sortDirection} onSort={onSort} align="right" />}
              {visible('setup') && <th className="px-3 py-3">Setup</th>}
              {visible('sparkline') && <th className="px-3 py-3">7d Chart</th>}
            </tr>
          </thead>
          <tbody>
            {coins.map((coin) => (
              <tr key={coin.id} className="group border-b border-base-border/60 last:border-0 hover:bg-base-raised">
                <td className="px-3 py-2.5">
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      onToggleWatch(coin.id);
                    }}
                    className="focus-ring text-neutral/50 hover:text-accent-glow"
                  >
                    <Star size={15} fill={isWatched(coin.id) ? 'currentColor' : 'none'} className={isWatched(coin.id) ? 'text-accent-glow' : ''} />
                  </button>
                </td>
                {visible('market_cap_rank') && <td className="px-3 py-2.5 font-mono text-xs text-neutral">{coin.market_cap_rank ?? '—'}</td>}
                <td className="px-3 py-2.5">
                  <Link href={`/coin/${coin.id}`} className="flex items-center gap-2.5">
                    {coin.image && <Image src={coin.image} alt="" width={24} height={24} className="rounded-full" unoptimized />}
                    <span className="font-medium text-base-50">{coin.name}</span>
                    <span className="font-mono text-xs uppercase text-neutral">{coin.symbol}</span>
                  </Link>
                </td>
                {visible('current_price') && (
                  <td className="px-3 py-2.5 text-right font-mono tabular-nums text-base-50">{formatUsd(coin.current_price)}</td>
                )}
                {visible('price_change_percentage_1h_in_currency') && (
                  <td className="px-3 py-2.5 text-right"><PriceChange value={coin.price_change_percentage_1h_in_currency} /></td>
                )}
                {visible('price_change_percentage_24h_in_currency') && (
                  <td className="px-3 py-2.5 text-right"><PriceChange value={coin.price_change_percentage_24h_in_currency ?? coin.price_change_percentage_24h} /></td>
                )}
                {visible('price_change_percentage_7d_in_currency') && (
                  <td className="px-3 py-2.5 text-right"><PriceChange value={coin.price_change_percentage_7d_in_currency} /></td>
                )}
                {visible('total_volume') && (
                  <td className="px-3 py-2.5 text-right font-mono tabular-nums text-neutral">{formatUsd(coin.total_volume, { compact: true })}</td>
                )}
                {visible('market_cap') && (
                  <td className="px-3 py-2.5 text-right font-mono tabular-nums text-neutral">{formatUsd(coin.market_cap, { compact: true })}</td>
                )}
                {visible('setup') && (
                  <td className="px-3 py-2.5">
                    <SetupBadge coin={coin} />
                  </td>
                )}
                {visible('sparkline') && (
                  <td className="px-3 py-2.5">
                    <Sparkline data={coin.sparkline_in_7d?.price} positive={(coin.price_change_percentage_7d_in_currency ?? 0) >= 0} />
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile card list */}
      <div className="flex flex-col gap-2 md:hidden">
        {coins.map((coin) => (
          <Link
            key={coin.id}
            href={`/coin/${coin.id}`}
            className="flex items-center gap-3 rounded-xl2 border border-base-border bg-base-surface p-3 active:bg-base-raised"
          >
            <button
              onClick={(e) => {
                e.preventDefault();
                onToggleWatch(coin.id);
              }}
              className="shrink-0 text-neutral/50"
            >
              <Star size={16} fill={isWatched(coin.id) ? 'currentColor' : 'none'} className={isWatched(coin.id) ? 'text-accent-glow' : ''} />
            </button>
            {coin.image && <Image src={coin.image} alt="" width={30} height={30} className="shrink-0 rounded-full" unoptimized />}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-sm font-medium text-base-50">{coin.name}</span>
                <span className="font-mono text-[11px] uppercase text-neutral">{coin.symbol}</span>
              </div>
              <div className="mt-0.5 flex items-center gap-2">
                <span className="font-mono text-xs tabular-nums text-neutral">{formatUsd(coin.current_price)}</span>
                <SetupBadge coin={coin} />
              </div>
            </div>
            <div className="flex shrink-0 flex-col items-end gap-1">
              <PriceChange value={coin.price_change_percentage_24h_in_currency ?? coin.price_change_percentage_24h} />
              <Sparkline data={coin.sparkline_in_7d?.price} width={70} height={24} positive={(coin.price_change_percentage_7d_in_currency ?? 0) >= 0} />
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}

function SortableHeader({
  label,
  columnKey,
  activeKey,
  sortDirection,
  onSort,
  align = 'left',
  className,
}: {
  label: string;
  columnKey: SortKey;
  activeKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
  align?: 'left' | 'right';
  className?: string;
}) {
  const active = columnKey === activeKey;
  return (
    <th className={cn('px-3 py-3 font-medium', className)}>
      <button
        onClick={() => onSort(columnKey)}
        className={cn(
          'focus-ring inline-flex items-center gap-1 hover:text-base-50',
          align === 'right' && 'w-full justify-end',
          active && 'text-base-50'
        )}
      >
        {label}
        {active ? (
          sortDirection === 'asc' ? (
            <ChevronUp size={12} />
          ) : (
            <ChevronDown size={12} />
          )
        ) : (
          <ChevronDown size={12} className="opacity-0 group-hover:opacity-30" />
        )}
      </button>
    </th>
  );
}
