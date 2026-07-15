'use client';

import * as TabsPrimitive from '@radix-ui/react-tabs';
import { cn } from '@/lib/utils';

export const Tabs = TabsPrimitive.Root;

export function TabsList({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.List>) {
  return (
    <TabsPrimitive.List
      className={cn('inline-flex items-center gap-1 rounded-lg border border-base-border bg-base-raised p-1', className)}
      {...props}
    />
  );
}

export function TabsTrigger({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      className={cn(
        'focus-ring rounded-md px-3 py-1.5 text-xs font-medium text-neutral transition-colors data-[state=active]:bg-base-border data-[state=active]:text-base-50',
        className
      )}
      {...props}
    />
  );
}

export const TabsContent = TabsPrimitive.Content;
