import { NextResponse } from 'next/server';
import { searchCoins } from '@/lib/coingecko';

export const revalidate = 300;

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const query = searchParams.get('q')?.trim();
  if (!query) return NextResponse.json({ coins: [] });

  try {
    const data = await searchCoins(query);
    return NextResponse.json({ coins: data.coins.slice(0, 8) });
  } catch (err) {
    console.error(err);
    return NextResponse.json({ error: 'Search failed' }, { status: 502 });
  }
}
