'use client';

import { useMemo } from 'react';
import { Check, Minus, TrendingDown, TrendingUp } from 'lucide-react';
import { useCoinChart } from '@/lib/hooks/useCoinDetail';
import { alignVolumesToCandles, detectSetup, toCandles } from '@/lib/indicators';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { cn } from '@/lib/utils';

export function SetupDetector({ coinId }: { coinId: string }) {
  const { data, isLoading } = useCoinChart(coinId, 365);

  const result = useMemo(() => {
    if (!data?.ohlc) return null;
    const candles = toCandles(data.ohlc);
    const volumes = alignVolumesToCandles(candles, data.volumes ?? []);
    return detectSetup(candles, volumes);
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Technical Setup Detector</CardTitle>
        <Badge tone="accent">Experimental</Badge>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {isLoading && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        )}

        {!isLoading && !result && (
          <p className="text-sm text-neutral">Not enough price history yet to detect a reliable setup for this asset.</p>
        )}

        {!isLoading && result && (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <BiasIcon bias={result.bias} />
              <span className="text-base font-semibold text-base-50">{result.label}</span>
              <ConfidenceBadge tier={result.confidence} />
            </div>

            <p className="text-sm leading-relaxed text-neutral">{result.summary}</p>

            <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
              {result.signals.map((signal) => (
                <div
                  key={signal.key}
                  className={cn(
                    'flex items-center gap-2 rounded-md border px-2.5 py-1.5 text-xs',
                    signal.fired ? 'border-accent/25 bg-accent/5 text-base-50' : 'border-base-border text-neutral/60'
                  )}
                >
                  {signal.fired ? <Check size={12} className="text-accent-glow" /> : <Minus size={12} />}
                  {signal.label}
                </div>
              ))}
            </div>

            <p className="text-[11px] leading-relaxed text-neutral/70">
              Statistical pattern-matching against this coin&apos;s own price history — not financial advice, and not a
              guarantee of future performance. Sample sizes on newer or low-volume tokens can be small; treat the win-rate
              above as directional context, not a precise probability.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function BiasIcon({ bias }: { bias: 'bullish' | 'bearish' | 'neutral' }) {
  if (bias === 'bullish') return <TrendingUp size={18} className="text-gain" />;
  if (bias === 'bearish') return <TrendingDown size={18} className="text-loss" />;
  return <Minus size={18} className="text-neutral" />;
}

function ConfidenceBadge({ tier }: { tier: 'Low' | 'Medium' | 'High' }) {
  const tone: 'gain' | 'accent' | 'neutral' = tier === 'High' ? 'gain' : tier === 'Medium' ? 'accent' : 'neutral';
  return <Badge tone={tone}>{tier} confluence</Badge>;
}
