import { NextResponse } from 'next/server';
import { fetchMarkets } from '@/lib/coingecko';

export const revalidate = 45;

export async function GET() {
  try {
    const [page1, page2] = await Promise.all([
      fetchMarkets({ page: 1, perPage: 250 }),
      fetchMarkets({ page: 2, perPage: 250 }),
    ]);
    return NextResponse.json([...page1, ...page2]);
  } catch (err) {
    console.error(err);
    return NextResponse.json({ error: 'Failed to fetch market data' }, { status: 502 });
  }
}
