'use client';

import { useCallback, useEffect, useState } from 'react';
import { getWatchlist, setWatchlist as persistWatchlist } from '@/lib/storage';

export function useWatchlist() {
  const [ids, setIds] = useState<string[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setIds(getWatchlist());
    setReady(true);
  }, []);

  const toggle = useCallback((id: string) => {
    setIds((prev) => {
      const next = prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id];
      persistWatchlist(next);
      return next;
    });
  }, []);

  const isWatched = useCallback((id: string) => ids.includes(id), [ids]);

  return { ids, toggle, isWatched, ready };
}
