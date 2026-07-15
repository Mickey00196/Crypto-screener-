'use client';

import { useState } from 'react';
import { Save, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/Dialog';
import type { FilterState, ScreenPreset, SortDirection, SortKey } from '@/lib/types';
import { cn } from '@/lib/utils';

export function PresetBar({
  presets,
  activePresetId,
  onSelect,
  onSave,
  onRemove,
  currentFilters,
  currentSort,
  currentDirection,
}: {
  presets: ScreenPreset[];
  activePresetId: string | null;
  onSelect: (preset: ScreenPreset) => void;
  onSave: (preset: Omit<ScreenPreset, 'id' | 'createdAt'>) => void;
  onRemove: (id: string) => void;
  currentFilters: FilterState;
  currentSort: SortKey;
  currentDirection: SortDirection;
}) {
  const [name, setName] = useState('');
  const [open, setOpen] = useState(false);

  function handleSave() {
    if (!name.trim()) return;
    onSave({ name: name.trim(), filters: currentFilters, sortKey: currentSort, sortDirection: currentDirection });
    setName('');
    setOpen(false);
  }

  return (
    <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1">
      {presets.map((preset) => (
        <div key={preset.id} className="group relative shrink-0">
          <button
            onClick={() => onSelect(preset)}
            className={cn(
              'focus-ring whitespace-nowrap rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors',
              activePresetId === preset.id
                ? 'border-accent bg-accent/10 text-accent-glow'
                : 'border-base-border bg-base-raised text-neutral hover:text-base-50'
            )}
          >
            {preset.name}
          </button>
          {!preset.builtIn && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove(preset.id);
              }}
              className="absolute -right-1 -top-1 hidden h-4 w-4 items-center justify-center rounded-full bg-loss text-white group-hover:flex"
            >
              <Trash2 size={9} />
            </button>
          )}
        </div>
      ))}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button size="sm" variant="ghost" className="shrink-0">
            <Save size={13} />
            Save screen
          </Button>
        </DialogTrigger>
        <DialogContent title="Save custom screen">
          <div className="flex flex-col gap-3">
            <Input
              autoFocus
              placeholder="e.g. My DeFi momentum screen"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSave()}
            />
            <p className="text-xs text-neutral">Saves your current filters and sort order to this browser for quick reuse.</p>
            <Button variant="accent" onClick={handleSave} disabled={!name.trim()}>
              Save preset
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
