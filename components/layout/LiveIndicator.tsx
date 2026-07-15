'use client';

import { useIsFetching } from '@tanstack/react-query';

export function LiveIndicator() {
  const isFetching = useIsFetching();

  return (
    <div className="hidden shrink-0 items-center gap-1.5 rounded-full border border-base-border bg-base-raised px-2.5 py-1 text-xs text-neutral md:flex">
      <span className={`h-1.5 w-1.5 rounded-full ${isFetching ? 'bg-accent animate-pulse-soft' : 'bg-gain'}`} />
      {isFetching ? 'Syncing' : 'Live'}
    </div>
  );
}
