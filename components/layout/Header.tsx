'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bookmark, Grid3x3, LayoutGrid } from 'lucide-react';
import { Logo } from '@/components/shared/Logo';
import { SearchBox } from './SearchBox';
import { cn } from '@/lib/utils';
import { LiveIndicator } from './LiveIndicator';

const NAV = [
  { href: '/', label: 'Screener', icon: LayoutGrid },
  { href: '/heatmap', label: 'Heatmap', icon: Grid3x3 },
  { href: '/watchlist', label: 'Watchlist', icon: Bookmark },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 border-b border-base-border bg-base-background/85 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-[1600px] items-center gap-4 px-4 md:px-6">
        <Link href="/" className="shrink-0">
          <Logo />
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
                  active ? 'bg-base-raised text-base-50' : 'text-neutral hover:text-base-50'
                )}
              >
                <item.icon size={15} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto hidden max-w-md flex-1 md:block">
          <SearchBox />
        </div>

        <LiveIndicator />
      </div>

      <div className="border-t border-base-border px-4 py-2 md:hidden">
        <SearchBox />
      </div>
    </header>
  );
}
