export interface TreemapInput {
  id: string;
  value: number;
}

export interface TreemapRect extends TreemapInput {
  x: number;
  y: number;
  w: number;
  h: number;
}

// Classic squarified treemap layout (Bruls, Huizing, van Wijk).
// Operates on a normalized [0,0,width,height] canvas.
export function squarify(items: TreemapInput[], width: number, height: number): TreemapRect[] {
  const total = items.reduce((sum, i) => sum + i.value, 0);
  if (total <= 0 || items.length === 0) return [];

  const scale = (width * height) / total;
  const sorted = [...items].sort((a, b) => b.value - a.value).map((i) => ({ ...i, area: i.value * scale }));

  const rects: TreemapRect[] = [];
  let x = 0;
  let y = 0;
  let w = width;
  let h = height;
  let row: typeof sorted = [];

  function worstRatio(rowItems: typeof sorted, length: number): number {
    const sum = rowItems.reduce((s, i) => s + i.area, 0);
    const maxA = Math.max(...rowItems.map((i) => i.area));
    const minA = Math.min(...rowItems.map((i) => i.area));
    return Math.max((length * length * maxA) / (sum * sum), (sum * sum) / (length * length * minA));
  }

  function layoutRow(rowItems: typeof sorted, horizontal: boolean) {
    const sum = rowItems.reduce((s, i) => s + i.area, 0);
    if (horizontal) {
      const rowHeight = sum / w;
      let cx = x;
      for (const item of rowItems) {
        const rw = item.area / rowHeight;
        rects.push({ id: item.id, value: item.value, x: cx, y, w: rw, h: rowHeight });
        cx += rw;
      }
      y += rowHeight;
      h -= rowHeight;
    } else {
      const colWidth = sum / h;
      let cy = y;
      for (const item of rowItems) {
        const rh = item.area / colWidth;
        rects.push({ id: item.id, value: item.value, x, y: cy, w: colWidth, h: rh });
        cy += rh;
      }
      x += colWidth;
      w -= colWidth;
    }
  }

  let remaining = [...sorted];
  while (remaining.length > 0) {
    const length = Math.min(w, h);
    const horizontal = w >= h;
    let i = 0;
    row = [remaining[0]!];
    while (i + 1 < remaining.length) {
      const next = [...row, remaining[i + 1]!];
      if (worstRatio(next, length) <= worstRatio(row, length)) {
        row = next;
        i++;
      } else break;
    }
    layoutRow(row, horizontal);
    remaining = remaining.slice(row.length);
  }

  return rects;
}
