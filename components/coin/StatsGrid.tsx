import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { formatUsd, formatCompact, formatPercent } from '@/lib/format';
import { PriceChange } from '@/components/shared/PriceChange';

function Stat({ label, value, sub }: { label: string; value: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[11px] uppercase tracking-wide text-neutral">{label}</span>
      <span className="font-mono text-sm tabular-nums text-base-50">{value}</span>
      {sub}
    </div>
  );
}

export function StatsGrid({ market }: { market: any }) {
  const supplyRatio = market.total_supply ? (market.circulating_supply / market.total_supply) * 100 : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Key Stats</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-x-4 gap-y-5 sm:grid-cols-3">
        <Stat label="Market Cap" value={formatUsd(market.market_cap?.usd, { compact: true })} />
        <Stat label="Fully Diluted Val." value={formatUsd(market.fully_diluted_valuation?.usd, { compact: true })} />
        <Stat label="24h Volume" value={formatUsd(market.total_volume?.usd, { compact: true })} />
        <Stat label="Circulating Supply" value={formatCompact(market.circulating_supply)} />
        <Stat label="Total Supply" value={formatCompact(market.total_supply)} />
        <Stat label="Max Supply" value={market.max_supply ? formatCompact(market.max_supply) : '∞'} />
        <Stat
          label="ATH"
          value={formatUsd(market.ath?.usd)}
          sub={<PriceChange value={market.ath_change_percentage?.usd} />}
        />
        <Stat
          label="ATL"
          value={formatUsd(market.atl?.usd)}
          sub={<PriceChange value={market.atl_change_percentage?.usd} />}
        />
        <Stat label="Circ. / Total Supply" value={supplyRatio !== null ? formatPercent(supplyRatio, { withSign: false }) : '—'} />
      </CardContent>
    </Card>
  );
}
