import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

export const Input = forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          'focus-ring h-9 w-full rounded-lg border border-base-border bg-base-raised px-3 text-sm text-base-50 placeholder:text-neutral/60',
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = 'Input';
