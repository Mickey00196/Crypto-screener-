import type { LucideIcon } from 'lucide-react';

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl2 border border-dashed border-base-border px-6 py-16 text-center animate-fade-in">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-base-raised text-neutral">
        <Icon size={22} />
      </div>
      <h3 className="text-sm font-semibold text-base-50">{title}</h3>
      <p className="max-w-sm text-sm text-neutral">{description}</p>
      {action}
    </div>
  );
}
