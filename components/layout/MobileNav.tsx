'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bookmark, LayoutGrid, Grid3x3 } from 'lucide-react';
import { cn } from '@/lib/utils';

const NAV = [
  { href: '/', label: 'Screener', icon: LayoutGrid },
  { href: '/heatmap', label: 'Heatmap', icon: Grid3x3 },
  { href: '/watchlist', label: 'Watchlist', icon: Bookmark },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 flex border-t border-base-border bg-base-background/95 backdrop-blur-md md:hidden">
      {NAV.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex flex-1 flex-col items-center gap-0.5 py-2.5 text-[11px] font-medium',
              active ? 'text-accent-glow' : 'text-neutral'
            )}
          >
            <item.icon size={18} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
