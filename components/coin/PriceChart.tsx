'use client';

import { useEffect, useRef, useState } from 'react';
import type { IChartApi, ISeriesApi } from 'lightweight-charts';
import { useCoinChart } from '@/lib/hooks/useCoinDetail';
import { Skeleton } from '@/components/ui/Skeleton';
import { cn } from '@/lib/utils';

const RANGES: { label: string; days: number | 'max' }[] = [
  { label: '24h', days: 1 },
  { label: '7d', days: 7 },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
  { label: '1y', days: 365 },
  { label: 'Max', days: 'max' },
];

export function PriceChart({ coinId }: { coinId: string }) {
  const [range, setRange] = useState<number | 'max'>(30);
  const { data, isLoading } = useCoinChart(coinId, range);
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Area'> | null>(null);

  useEffect(() => {
    let disposed = false;
    async function init() {
      if (!containerRef.current) return;
      const { createChart } = await import('lightweight-charts');
      if (disposed || !containerRef.current) return;

      const chart = createChart(containerRef.current, {
        layout: { background: { color: 'transparent' }, textColor: '#8a92a3', fontFamily: 'var(--font-mono)' },
        grid: { vertLines: { color: '#1f2430' }, horzLines: { color: '#1f2430' } },
        rightPriceScale: { borderColor: '#1f2430' },
        timeScale: { borderColor: '#1f2430', timeVisible: true, secondsVisible: false },
        crosshair: { mode: 0 },
        height: 360,
        autoSize: true,
      });

      const series = chart.addAreaSeries({
        lineColor: '#5b8cff',
        topColor: 'rgba(91,140,255,0.28)',
        bottomColor: 'rgba(91,140,255,0.02)',
        lineWidth: 2,
        priceLineVisible: false,
      });

      chartRef.current = chart;
      seriesRef.current = series;
    }
    init();

    return () => {
      disposed = true;
      chartRef.current?.remove();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current || !data?.prices) return;
    const points = data.prices.map(([time, value]) => ({ time: Math.floor(time / 1000) as any, value }));
    // lightweight-charts requires strictly ascending, de-duplicated time values
    const seen = new Set<number>();
    const clean = points.filter((p) => {
      if (seen.has(p.time)) return false;
      seen.add(p.time);
      return true;
    });
    seriesRef.current.setData(clean);
    chartRef.current?.timeScale().fitContent();

    const first = clean[0]?.value ?? 0;
    const last = clean[clean.length - 1]?.value ?? 0;
    const positive = last >= first;
    seriesRef.current.applyOptions({
      lineColor: positive ? '#2fd47a' : '#ff5c72',
      topColor: positive ? 'rgba(47,212,122,0.28)' : 'rgba(255,92,114,0.28)',
      bottomColor: positive ? 'rgba(47,212,122,0.02)' : 'rgba(255,92,114,0.02)',
    });
  }, [data]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-1">
        {RANGES.map((r) => (
          <button
            key={r.label}
            onClick={() => setRange(r.days)}
            className={cn(
              'focus-ring rounded-md px-2.5 py-1 text-xs font-medium transition-colors',
              range === r.days ? 'bg-base-border text-base-50' : 'text-neutral hover:text-base-50'
            )}
          >
            {r.label}
          </button>
        ))}
      </div>
      <div className="relative h-[360px] w-full">
        {isLoading && <Skeleton className="absolute inset-0" />}
        <div ref={containerRef} className="h-full w-full" />
      </div>
    </div>
  );
}
