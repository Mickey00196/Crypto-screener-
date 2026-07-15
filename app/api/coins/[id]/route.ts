import { NextResponse } from 'next/server';
import { fetchCoinDetail } from '@/lib/coingecko';

export const revalidate = 45;

export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const data = await fetchCoinDetail(id);
    return NextResponse.json(data);
  } catch (err) {
    console.error(err);
    return NextResponse.json({ error: 'Failed to fetch coin detail' }, { status: 502 });
  }
}
