import { cn } from '@/lib/utils';

type Tone = 'neutral' | 'gain' | 'loss' | 'accent';

const toneClasses: Record<Tone, string> = {
  neutral: 'bg-base-raised text-neutral border-base-border',
  gain: 'bg-gain-bg text-gain border-transparent',
  loss: 'bg-loss-bg text-loss border-transparent',
  accent: 'bg-accent/10 text-accent-glow border-accent/30',
};

export function Badge({
  tone = 'neutral',
  className,
  children,
}: {
  tone?: Tone;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium',
        toneClasses[tone],
        className
      )}
    >
      {children}
    </span>
  );
}
