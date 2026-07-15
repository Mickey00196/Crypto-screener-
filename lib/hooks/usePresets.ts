'use client';

import { useCallback, useEffect, useState } from 'react';
import { BUILT_IN_PRESETS } from '@/lib/presets';
import { getCustomPresets, setCustomPresets } from '@/lib/storage';
import type { ScreenPreset } from '@/lib/types';

export function usePresets() {
  const [custom, setCustom] = useState<ScreenPreset[]>([]);

  useEffect(() => {
    setCustom(getCustomPresets());
  }, []);

  const save = useCallback((preset: Omit<ScreenPreset, 'id' | 'createdAt'>) => {
    const next: ScreenPreset = {
      ...preset,
      id: `custom-${Date.now()}`,
      createdAt: Date.now(),
    };
    setCustom((prev) => {
      const updated = [...prev, next];
      setCustomPresets(updated);
      return updated;
    });
    return next;
  }, []);

  const remove = useCallback((id: string) => {
    setCustom((prev) => {
      const updated = prev.filter((p) => p.id !== id);
      setCustomPresets(updated);
      return updated;
    });
  }, []);

  return { presets: [...BUILT_IN_PRESETS, ...custom], custom, save, remove };
}
