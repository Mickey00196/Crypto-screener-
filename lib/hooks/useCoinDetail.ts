'use client';

import { useQuery } from '@tanstack/react-query';

export function useCoinDetail(id: string) {
  return useQuery({
    queryKey: ['coin', id],
    queryFn: async () => {
      const res = await fetch(`/api/coins/${id}`);
      if (!res.ok) throw new Error('Failed to load coin');
      return res.json();
    },
    refetchInterval: 45_000,
  });
}

export function useCoinChart(id: string, days: number | 'max') {
  return useQuery({
    queryKey: ['coin-chart', id, days],
    queryFn: async () => {
      const res = await fetch(`/api/coins/${id}/chart?days=${days}`);
      if (!res.ok) throw new Error('Failed to load chart');
      return res.json() as Promise<{
        prices: [number, number][];
        volumes: [number, number][];
        ohlc: [number, number, number, number, number][];
      }>;
    },
    staleTime: 60_000,
  });
}
