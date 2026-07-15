'use client';

import { useMemo } from 'react';

export function Sparkline({
  data,
  width = 120,
  height = 36,
  positive,
}: {
  data: number[] | undefined;
  width?: number;
  height?: number;
  positive: boolean;
}) {
  const path = useMemo(() => {
    if (!data || data.length < 2) return null;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const step = width / (data.length - 1);
    const points = data.map((v, i) => {
      const x = i * step;
      const y = height - ((v - min) / range) * height;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    });
    return `M${points.join(' L')}`;
  }, [data, width, height]);

  if (!path) {
    return <div className="opacity-30" style={{ width, height }} />;
  }

  const color = positive ? '#2fd47a' : '#ff5c72';

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
      <path d={path} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
