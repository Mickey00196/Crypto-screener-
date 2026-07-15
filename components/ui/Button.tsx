'use client';

import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

type Variant = 'default' | 'outline' | 'ghost' | 'accent';
type Size = 'sm' | 'md' | 'icon';

const variantClasses: Record<Variant, string> = {
  default: 'bg-base-raised text-base-50 hover:bg-base-borderLight border border-base-border',
  outline: 'bg-transparent border border-base-border text-base-50 hover:bg-base-raised',
  ghost: 'bg-transparent text-neutral hover:text-base-50 hover:bg-base-raised',
  accent: 'bg-accent text-white hover:bg-accent-glow shadow-glow',
};

const sizeClasses: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-9 px-4 text-sm',
  icon: 'h-9 w-9',
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'focus-ring inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition-colors duration-150 disabled:pointer-events-none disabled:opacity-40',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';
