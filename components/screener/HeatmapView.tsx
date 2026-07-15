'use client';

import { useCallback, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import type { Coin } from '@/lib/types';
import { formatUsd, formatPercent } from '@/lib/format';
import { squarify } from '@/lib/treemap';
import { Skeleton } from '@/components/ui/Skeleton';

function colorForChange(change: number | null | undefined): string {
  const v = change ?? 0;
  const clamped = Math.max(-15, Math.min(15, v));
  const intensity = Math.abs(clamped) / 15;
  if (v >= 0) {
    // gain scale
    const l = 38 - intensity * 16;
    return `hsl(151, 60%, ${l}%)`;
  }
  const l = 40 - intensity * 15;
  return `hsl(351, 65%, ${l}%)`;
}

export function HeatmapView({ coins, loading }: { coins: Coin[]; loading: boolean }) {
  const [size, setSize] = useState({ width: 1200, height: 600 });
  const observerRef = useRef<ResizeObserver | null>(null);

  // A callback ref (rather than a mount-time effect) so we re-measure whenever the
  // container actually appears in the DOM — including the loading → loaded swap,
  // when the ref-bearing element doesn't exist yet on first mount.
  const containerRef = useCallback((node: HTMLDivElement | null) => {
    observerRef.current?.disconnect();
    observerRef.current = null;
    if (!node) return;
    const update = () => setSize({ width: node.clientWidth, height: Math.max(node.clientWidth * 0.55, 420) });
    update();
    const ro = new ResizeObserver(update);
    ro.observe(node);
    observerRef.current = ro;
  }, []);

  const rects = useMemo(() => {
    const top = coins.filter((c) => c.market_cap > 0).slice(0, 120);
    return squarify(
      top.map((c) => ({ id: c.id, value: Math.sqrt(c.market_cap) })),
      size.width,
      size.height
    );
  }, [coins, size]);

  const byId = useMemo(() => new Map(coins.map((c) => [c.id, c])), [coins]);

  if (loading) {
    return <Skeleton className="h-[420px] w-full" />;
  }

  return (
    <div ref={containerRef} className="relative w-full overflow-hidden rounded-xl2 border border-base-border" style={{ height: size.height }}>
      {rects.map((rect) => {
        const coin = byId.get(rect.id);
        if (!coin) return null;
        const change = coin.price_change_percentage_24h_in_currency ?? coin.price_change_percentage_24h;
        const showLabel = rect.w > 55 && rect.h > 36;
        return (
          <Link
            key={rect.id}
            href={`/coin/${coin.id}`}
            className="absolute flex flex-col items-center justify-center overflow-hidden border border-black/20 p-1 text-center transition-[filter] hover:z-10 hover:brightness-125"
            style={{
              left: rect.x,
              top: rect.y,
              width: rect.w,
              height: rect.h,
              backgroundColor: colorForChange(change),
            }}
            title={`${coin.name} — ${formatPercent(change)}`}
          >
            {showLabel ? (
              <>
                <span className="truncate text-xs font-semibold text-white drop-shadow">{coin.symbol.toUpperCase()}</span>
                <span className="font-mono text-[11px] text-white/90 drop-shadow">{formatPercent(change)}</span>
                {rect.w > 90 && rect.h > 60 && (
                  <span className="mt-0.5 font-mono text-[10px] text-white/70">{formatUsd(coin.current_price)}</span>
                )}
              </>
            ) : rect.w > 24 && rect.h > 18 ? (
              <span className="truncate text-[10px] font-semibold text-white drop-shadow">{coin.symbol.toUpperCase()}</span>
            ) : null}
          </Link>
        );
      })}
    </div>
  );
}
