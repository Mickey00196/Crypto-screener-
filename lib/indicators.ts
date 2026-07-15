import type { ConfidenceTier, SetupResult, SignalResult } from './types';

export type Candle = { time: number; open: number; high: number; low: number; close: number };

export function toCandles(ohlc: [number, number, number, number, number][]): Candle[] {
  return ohlc.map(([time, open, high, low, close]) => ({ time, open, high, low, close }));
}

/** Aligns a coarser/finer volume series (from market_chart) to each OHLC candle by nearest prior timestamp. */
export function alignVolumesToCandles(candles: Candle[], volumeSeries: [number, number][]): number[] {
  if (volumeSeries.length === 0) return candles.map(() => 0);
  let vi = 0;
  return candles.map((candle) => {
    while (vi + 1 < volumeSeries.length && volumeSeries[vi + 1]![0] <= candle.time) vi++;
    return volumeSeries[vi]?.[1] ?? 0;
  });
}

export function sma(values: number[], period: number): (number | null)[] {
  const out: (number | null)[] = new Array(values.length).fill(null);
  let sum = 0;
  for (let i = 0; i < values.length; i++) {
    sum += values[i]!;
    if (i >= period) sum -= values[i - period]!;
    if (i >= period - 1) out[i] = sum / period;
  }
  return out;
}

export function ema(values: number[], period: number): (number | null)[] {
  const out: (number | null)[] = new Array(values.length).fill(null);
  const k = 2 / (period + 1);
  let prev: number | null = null;
  for (let i = 0; i < values.length; i++) {
    const v = values[i]!;
    if (prev === null) {
      if (i >= period - 1) {
        const slice = values.slice(i - period + 1, i + 1);
        prev = slice.reduce((a, b) => a + b, 0) / period;
        out[i] = prev;
      }
    } else {
      prev = v * k + prev * (1 - k);
      out[i] = prev;
    }
  }
  return out;
}

export function rsi(values: number[], period = 14): (number | null)[] {
  const out: (number | null)[] = new Array(values.length).fill(null);
  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 1; i < values.length; i++) {
    const change = values[i]! - values[i - 1]!;
    const gain = Math.max(change, 0);
    const loss = Math.max(-change, 0);
    if (i <= period) {
      avgGain += gain;
      avgLoss += loss;
      if (i === period) {
        avgGain /= period;
        avgLoss /= period;
        out[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
      }
    } else {
      avgGain = (avgGain * (period - 1) + gain) / period;
      avgLoss = (avgLoss * (period - 1) + loss) / period;
      out[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
    }
  }
  return out;
}

export function macd(values: number[], fast = 12, slow = 26, signalPeriod = 9) {
  const emaFast = ema(values, fast);
  const emaSlow = ema(values, slow);
  const macdLine: (number | null)[] = values.map((_, i) =>
    emaFast[i] !== null && emaSlow[i] !== null ? emaFast[i]! - emaSlow[i]! : null
  );
  const cleaned = macdLine.map((v) => v ?? 0);
  const signalLine = ema(cleaned, signalPeriod).map((v, i) => (macdLine[i] === null ? null : v));
  const histogram = macdLine.map((v, i) => (v !== null && signalLine[i] !== null ? v - signalLine[i]! : null));
  return { macdLine, signalLine, histogram };
}

export function obv(closes: number[], volumes: number[]): number[] {
  const out: number[] = [0];
  for (let i = 1; i < closes.length; i++) {
    const prev = out[i - 1]!;
    if (closes[i]! > closes[i - 1]!) out.push(prev + volumes[i]!);
    else if (closes[i]! < closes[i - 1]!) out.push(prev - volumes[i]!);
    else out.push(prev);
  }
  return out;
}

interface SignalFlags {
  breakout: boolean[];
  volumeSpike: boolean[];
  goldenCross: boolean[];
  deathCross: boolean[];
  rsiOversoldBounce: boolean[];
  rsiOverboughtReject: boolean[];
  obvRising: boolean[];
  higherHighsLows: boolean[];
}

function computeFlags(candles: Candle[], volumes: number[]): SignalFlags {
  const n = candles.length;
  const closes = candles.map((c) => c.close);
  const highs = candles.map((c) => c.high);
  const lows = candles.map((c) => c.low);

  const sma20 = sma(closes, 20);
  const sma50 = sma(closes, 50);
  const sma200 = sma(closes, 200);
  const rsi14 = rsi(closes, 14);
  const obvSeries = obv(closes, volumes);
  const obvSma = sma(obvSeries, 10);
  const volAvg20 = sma(volumes, 20);

  const breakout = new Array(n).fill(false);
  const volumeSpike = new Array(n).fill(false);
  const goldenCross = new Array(n).fill(false);
  const deathCross = new Array(n).fill(false);
  const rsiOversoldBounce = new Array(n).fill(false);
  const rsiOverboughtReject = new Array(n).fill(false);
  const obvRising = new Array(n).fill(false);
  const higherHighsLows = new Array(n).fill(false);

  for (let i = 1; i < n; i++) {
    if (volAvg20[i] && volumes[i]! >= 1.5 * volAvg20[i]!) volumeSpike[i] = true;

    if (i >= 21) {
      const priorHigh = Math.max(...highs.slice(i - 20, i));
      if (closes[i]! > priorHigh) breakout[i] = true;
    }

    if (sma50[i] !== null && sma50[i - 1] !== null && sma200[i] !== null && sma200[i - 1] !== null) {
      if (sma50[i - 1]! <= sma200[i - 1]! && sma50[i]! > sma200[i]!) goldenCross[i] = true;
      if (sma50[i - 1]! >= sma200[i - 1]! && sma50[i]! < sma200[i]!) deathCross[i] = true;
    }

    if (rsi14[i] !== null) {
      if (rsi14[i]! < 35 && rsi14[i]! > (rsi14[i - 1] ?? 0)) rsiOversoldBounce[i] = true;
      if (rsi14[i]! > 65 && rsi14[i]! < (rsi14[i - 1] ?? 100)) rsiOverboughtReject[i] = true;
    }

    if (obvSma[i] !== null && obvSma[i - 5 < 0 ? 0 : i - 5] !== null) {
      obvRising[i] = obvSma[i]! > obvSma[Math.max(0, i - 5)]!;
    }

    if (i >= 10) {
      const recentHighs = highs.slice(i - 5, i + 1);
      const priorHighs = highs.slice(i - 10, i - 5);
      const recentLows = lows.slice(i - 5, i + 1);
      const priorLows = lows.slice(i - 10, i - 5);
      const hh = Math.max(...recentHighs) > Math.max(...priorHighs);
      const hl = Math.min(...recentLows) > Math.min(...priorLows);
      higherHighsLows[i] = hh && hl;
    }

    if (sma20[i] !== null) {
      // sma20 computed above; kept for potential future short-term trend checks
    }
  }

  return { breakout, volumeSpike, goldenCross, deathCross, rsiOversoldBounce, rsiOverboughtReject, obvRising, higherHighsLows };
}

/**
 * Backtests a boolean signal against this coin's own price history: of the times
 * the signal fired historically, what fraction of the time was price higher
 * `forwardDays` later, and by how much on average. This is a real (if small-n)
 * per-asset stat, not a cross-market lookup table — sample size is shown so
 * users can judge how much to trust it.
 */
function backtestSignal(flags: boolean[], closes: number[], forwardDays: number) {
  const returns: number[] = [];
  for (let i = 0; i < flags.length - forwardDays; i++) {
    if (flags[i]) {
      const ret = (closes[i + forwardDays]! - closes[i]!) / closes[i]!;
      returns.push(ret);
    }
  }
  if (returns.length === 0) return { winRate: null, avgMove: null, sampleSize: 0 };
  const wins = returns.filter((r) => r > 0).length;
  const avgMove = returns.reduce((a, b) => a + b, 0) / returns.length;
  return { winRate: (wins / returns.length) * 100, avgMove: avgMove * 100, sampleSize: returns.length };
}

const SIGNAL_META: Record<keyof SignalFlags, { label: string; bias: 'bullish' | 'bearish' }> = {
  breakout: { label: 'Range breakout', bias: 'bullish' },
  volumeSpike: { label: 'Volume ≥1.5× 20-period avg', bias: 'bullish' },
  goldenCross: { label: 'Golden cross (50MA > 200MA)', bias: 'bullish' },
  deathCross: { label: 'Death cross (50MA < 200MA)', bias: 'bearish' },
  rsiOversoldBounce: { label: 'RSI bouncing from oversold', bias: 'bullish' },
  rsiOverboughtReject: { label: 'RSI rejecting from overbought', bias: 'bearish' },
  obvRising: { label: 'OBV trending up (accumulation)', bias: 'bullish' },
  higherHighsLows: { label: 'Higher highs / higher lows', bias: 'bullish' },
};

export function detectSetup(candles: Candle[], volumes: number[]): SetupResult | null {
  if (candles.length < 30) return null;
  const closes = candles.map((c) => c.close);
  const flags = computeFlags(candles, volumes);
  const lastIdx = candles.length - 1;

  const signals: SignalResult[] = [];
  let bullScore = 0;
  let bearScore = 0;
  let primaryKey: keyof SignalFlags | null = null;

  (Object.keys(SIGNAL_META) as Array<keyof SignalFlags>).forEach((key) => {
    const fired = flags[key][lastIdx] ?? false;
    const meta = SIGNAL_META[key];
    if (fired) {
      if (meta.bias === 'bullish') bullScore += 1;
      else bearScore += 1;
      if (!primaryKey) primaryKey = key;
    }
    signals.push({ key, label: meta.label, fired, detail: fired ? 'Active on latest candle' : 'Not currently active' });
  });

  const netScore = bullScore - bearScore;
  const bias: 'bullish' | 'bearish' | 'neutral' = netScore > 0 ? 'bullish' : netScore < 0 ? 'bearish' : 'neutral';
  const agreeingCount = Math.max(bullScore, bearScore);

  let confidence: ConfidenceTier = 'Low';
  if (agreeingCount >= 4) confidence = 'High';
  else if (agreeingCount >= 2) confidence = 'Medium';

  let label = 'No clear setup';
  if (bias === 'bullish' && flags.breakout[lastIdx] && flags.volumeSpike[lastIdx]) label = 'Bullish breakout, volume-confirmed';
  else if (bias === 'bullish' && flags.goldenCross[lastIdx]) label = 'Golden cross forming';
  else if (bias === 'bullish' && flags.rsiOversoldBounce[lastIdx]) label = 'Bouncing from oversold';
  else if (bias === 'bullish' && flags.higherHighsLows[lastIdx]) label = 'Uptrend structure intact';
  else if (bias === 'bearish' && flags.deathCross[lastIdx]) label = 'Death cross forming';
  else if (bias === 'bearish' && flags.rsiOverboughtReject[lastIdx]) label = 'Rejecting from overbought';
  else if (bias === 'bullish') label = 'Mild bullish confluence';
  else if (bias === 'bearish') label = 'Mild bearish confluence';

  // Backtest the primary signal (or the breakout signal by default) against this coin's own history.
  const backtestKey: keyof SignalFlags = flags.breakout[lastIdx]
    ? 'breakout'
    : (primaryKey as keyof SignalFlags | null) ?? 'higherHighsLows';
  const bt = backtestSignal(flags[backtestKey], closes, 5);

  const summary =
    bias === 'neutral'
      ? "No dominant signal cluster right now — price action doesn't show clean confluence in either direction."
      : `${label}. Historically on this asset, when "${SIGNAL_META[backtestKey].label}" fired, price was higher 5 days later in ${
          bt.winRate !== null ? bt.winRate.toFixed(0) : '—'
        }% of ${bt.sampleSize} past occurrences (avg move ${bt.avgMove !== null ? (bt.avgMove >= 0 ? '+' : '') + bt.avgMove.toFixed(1) : '—'}%). Small sample — pattern-matching against this coin's own history, not a guarantee.`;

  return {
    label,
    bias,
    confidence,
    score: netScore,
    winRate: bt.winRate,
    avgMove: bt.avgMove,
    sampleSize: bt.sampleSize,
    signals,
    summary,
  };
}
