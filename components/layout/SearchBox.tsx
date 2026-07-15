'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, X } from 'lucide-react';
import Image from 'next/image';
import { useDebounce } from '@/lib/hooks/useDebounce';
import { cn } from '@/lib/utils';

interface SearchResult {
  id: string;
  name: string;
  symbol: string;
  market_cap_rank: number | null;
  thumb: string;
}

export function SearchBox({ className }: { className?: string }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const debounced = useDebounce(query, 200);
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (!debounced.trim()) {
      setResults([]);
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetch(`/api/search?q=${encodeURIComponent(debounced)}`)
      .then((r) => r.json())
      .then((data) => {
        if (!cancelled) setResults(data.coins ?? []);
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [debounced]);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  function selectCoin(id: string) {
    setOpen(false);
    setQuery('');
    router.push(`/coin/${id}`);
  }

  return (
    <div ref={containerRef} className={cn('relative w-full', className)}>
      <div className="relative">
        <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-neutral" />
        <input
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder="Search coins, symbols, or contract address..."
          className="focus-ring h-9 w-full rounded-lg border border-base-border bg-base-raised pl-9 pr-8 text-sm text-base-50 placeholder:text-neutral/60"
        />
        {query && (
          <button
            onClick={() => setQuery('')}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-neutral hover:text-base-50"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {open && query.trim() && (
        <div className="absolute left-0 right-0 top-11 z-40 max-h-80 overflow-y-auto rounded-lg border border-base-border bg-base-raised shadow-panel animate-slide-up">
          {loading && <div className="px-3 py-3 text-xs text-neutral">Searching…</div>}
          {!loading && results.length === 0 && <div className="px-3 py-3 text-xs text-neutral">No matches for &ldquo;{query}&rdquo;</div>}
          {!loading &&
            results.map((coin) => (
              <button
                key={coin.id}
                onClick={() => selectCoin(coin.id)}
                className="flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm hover:bg-base-border"
              >
                {coin.thumb && <Image src={coin.thumb} alt="" width={18} height={18} className="rounded-full" unoptimized />}
                <span className="text-base-50">{coin.name}</span>
                <span className="font-mono text-xs uppercase text-neutral">{coin.symbol}</span>
                {coin.market_cap_rank && <span className="ml-auto text-xs text-neutral">#{coin.market_cap_rank}</span>}
              </button>
            ))}
        </div>
      )}
    </div>
  );
}
