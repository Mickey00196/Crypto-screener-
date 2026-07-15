'use client';

import Image from 'next/image';
import { useState } from 'react';
import { ArrowLeft, Star } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useCoinDetail } from '@/lib/hooks/useCoinDetail';
import { useWatchlist } from '@/lib/hooks/useWatchlist';
import { formatUsd } from '@/lib/format';
import { PriceChange } from '@/components/shared/PriceChange';
import { PriceChart } from '@/components/coin/PriceChart';
import { StatsGrid } from '@/components/coin/StatsGrid';
import { SetupDetector } from '@/components/coin/SetupDetector';
import { ExplorerLinks } from '@/components/coin/ExplorerLinks';
import { Skeleton } from '@/components/ui/Skeleton';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export default function CoinDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { data, isLoading, isError } = useCoinDetail(id);
  const { isWatched, toggle } = useWatchlist();
  const [descExpanded, setDescExpanded] = useState(false);

  if (isError) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <p className="text-sm text-neutral">Couldn&apos;t load this coin. It may not exist or the data provider is temporarily unavailable.</p>
        <Link href="/" className="mt-4 inline-flex items-center gap-1.5 text-sm text-accent-glow">
          <ArrowLeft size={14} /> Back to screener
        </Link>
      </div>
    );
  }

  const market = data?.market_data;
  const description: string = data?.description?.en ?? '';
  const plainDescription = description.replace(/<[^>]*>/g, '');

  return (
    <div className="mx-auto flex max-w-[1200px] flex-col gap-5 px-4 py-5 md:px-6 md:py-6">
      <Link href="/" className="flex w-fit items-center gap-1.5 text-xs text-neutral hover:text-base-50">
        <ArrowLeft size={13} /> Back to screener
      </Link>

      {isLoading || !data ? (
        <div className="flex items-center gap-3">
          <Skeleton className="h-12 w-12 rounded-full" />
          <div className="flex flex-col gap-2">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap items-center gap-4">
          {data.image?.large && <Image src={data.image.large} alt="" width={48} height={48} className="rounded-full" unoptimized />}
          <div className="flex flex-col gap-0.5">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold text-base-50">{data.name}</h1>
              <span className="font-mono text-sm uppercase text-neutral">{data.symbol}</span>
              {data.market_cap_rank && <Badge>Rank #{data.market_cap_rank}</Badge>}
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-2xl font-semibold tabular-nums text-base-50">{formatUsd(market?.current_price?.usd)}</span>
              <PriceChange value={market?.price_change_percentage_24h} size="md" />
            </div>
          </div>
          <button
            onClick={() => toggle(data.id)}
            className="focus-ring ml-auto flex items-center gap-1.5 rounded-lg border border-base-border bg-base-raised px-3 py-2 text-sm text-neutral hover:text-base-50"
          >
            <Star size={15} fill={isWatched(data.id) ? 'currentColor' : 'none'} className={isWatched(data.id) ? 'text-accent-glow' : ''} />
            {isWatched(data.id) ? 'Watching' : 'Watch'}
          </button>
        </div>
      )}

      <Card>
        <CardContent>
          <PriceChart coinId={id} />
        </CardContent>
      </Card>

      <SetupDetector coinId={id} />

      {market && <StatsGrid market={market} />}

      {plainDescription && (
        <Card>
          <CardContent>
            <h3 className="mb-2 text-sm font-semibold text-base-50">About {data.name}</h3>
            <p className={`text-sm leading-relaxed text-neutral ${descExpanded ? '' : 'line-clamp-4'}`}>{plainDescription}</p>
            {plainDescription.length > 300 && (
              <button onClick={() => setDescExpanded((v) => !v)} className="mt-2 text-xs font-medium text-accent-glow">
                {descExpanded ? 'Show less' : 'Read more'}
              </button>
            )}
          </CardContent>
        </Card>
      )}

      {data?.links && <ExplorerLinks links={data.links} />}
    </div>
  );
}
