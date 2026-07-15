'use client';

import * as CheckboxPrimitive from '@radix-ui/react-checkbox';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Checkbox({ className, ...props }: React.ComponentProps<typeof CheckboxPrimitive.Root>) {
  return (
    <CheckboxPrimitive.Root
      className={cn(
        'focus-ring flex h-4 w-4 items-center justify-center rounded border border-base-border bg-base-raised data-[state=checked]:border-accent data-[state=checked]:bg-accent',
        className
      )}
      {...props}
    >
      <CheckboxPrimitive.Indicator>
        <Check size={12} className="text-white" />
      </CheckboxPrimitive.Indicator>
    </CheckboxPrimitive.Root>
  );
}
