'use client';

import { Columns3 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Checkbox } from '@/components/ui/Checkbox';
import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger } from '@/components/ui/DropdownMenu';
import type { ColumnConfig } from '@/lib/types';

export function ColumnCustomizer({
  columns,
  onChange,
}: {
  columns: ColumnConfig[];
  onChange: (columns: ColumnConfig[]) => void;
}) {
  function toggle(key: ColumnConfig['key']) {
    onChange(columns.map((c) => (c.key === key ? { ...c, visible: !c.visible } : c)));
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button size="sm" variant="outline">
          <Columns3 size={13} />
          Columns
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="max-h-80 overflow-y-auto">
        {columns
          .filter((c) => c.key !== 'watchlist' && c.key !== 'name')
          .map((col) => (
            <label
              key={col.key}
              className="flex cursor-pointer items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm text-base-50 hover:bg-base-border"
            >
              <Checkbox checked={col.visible} onCheckedChange={() => toggle(col.key)} />
              {col.label || col.key}
            </label>
          ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
