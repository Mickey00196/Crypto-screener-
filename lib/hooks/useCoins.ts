'use client';

import { useQuery } from '@tanstack/react-query';
import type { Coin } from '@/lib/types';

async function getCoins(): Promise<Coin[]> {
  const res = await fetch('/api/coins', { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load market data');
  return res.json();
}

export function useCoins() {
  return useQuery({
    queryKey: ['coins'],
    queryFn: getCoins,
    refetchInterval: 45_000,
    staleTime: 30_000,
  });
}
