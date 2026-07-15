import { NextResponse } from 'next/server';
import { fetchMarketChart, fetchOHLC } from '@/lib/coingecko';

export const revalidate = 120;

export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { searchParams } = new URL(req.url);
  const days = searchParams.get('days') ?? '200';

  try {
    const [chart, ohlc] = await Promise.all([
      fetchMarketChart(id, days === 'max' ? 'max' : Number(days)),
      fetchOHLC(id, days === 'max' ? 365 : Math.min(Number(days), 365)),
    ]);
    return NextResponse.json({ prices: chart.prices, volumes: chart.total_volumes, ohlc });
  } catch (err) {
    console.error(err);
    return NextResponse.json({ error: 'Failed to fetch chart data' }, { status: 502 });
  }
}
