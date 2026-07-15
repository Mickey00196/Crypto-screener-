import { ArrowDown, ArrowUp } from 'lucide-react';
import { formatPercent, changeTone } from '@/lib/format';
import { cn } from '@/lib/utils';

export function PriceChange({ value, size = 'sm' }: { value: number | null | undefined; size?: 'sm' | 'md' }) {
  const tone = changeTone(value);
  return (
    <span
      className={cn(
        'inline-flex items-center gap-0.5 font-mono tabular-nums',
        size === 'sm' ? 'text-xs' : 'text-sm',
        tone === 'gain' && 'text-gain',
        tone === 'loss' && 'text-loss',
        tone === 'neutral' && 'text-neutral'
      )}
    >
      {tone === 'gain' && <ArrowUp size={size === 'sm' ? 10 : 12} />}
      {tone === 'loss' && <ArrowDown size={size === 'sm' ? 10 : 12} />}
      {formatPercent(value)}
    </span>
  );
}
