// src/temp/stockForecast.mock.ts

// 1点 = 1ヶ月（YYYY-MM）
import type { StockForecastData, Series, HistoricalPrediction } from "@/libs/chart/types";

/** 文字列 "YYYY-MM" を配列で生成（months 分） */
function buildMonthLabels(startYm: string, months: number): string[] {
    const [y, m] = startYm.split("-").map(Number);
    const start = new Date(y, m - 1, 1);
    const out: string[] = [];
    for (let i = 0; i < months; i++) {
        const d = new Date(start);
        d.setMonth(d.getMonth() + i);
        out.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
    }
    return out;
}

/** 簡易シード乱数（ticker で再現性） */
function rng(seed: number) {
    let s = seed >>> 0;
    return () => {
        s = (s * 1664525 + 1013904223) >>> 0;
        return s / 0xffffffff;
    };
}

function hash(s: string): number {
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) {
        h ^= s.charCodeAt(i);
        h = (h * 16777619) >>> 0;
    }
    return h >>> 0;
}

export function makeMockForecast(
    ticker: string,
    startYm = "2022-01",
    months = 48 // 3年過去 + 1年未来
): StockForecastData {
    const labels = buildMonthLabels(startYm, months);

    const seed = hash(ticker);
    const rand = rng(seed);

    // 実測（最初の 36 ヶ月＝過去3年分を埋める）
    const actual: Series = Array(months).fill(null);
    let v = 8000 + Math.floor(rand() * 6000); // 初期株価（円）
    for (let i = 0; i < Math.min(months - 12, months); i++) {
        // ノイズ＋ゆるい上昇トレンド
        const drift = 80 + Math.floor(rand() * 60);         // 月あたり上昇
        const noise = Math.floor((rand() - 0.5) * 400);      // ノイズ
        v = Math.max(500, v + drift + noise);
        actual[i] = v;
    }

    // predictStart = 最後の実測の “次”
    const lastActualIdx = actual.findLastIndex((x) => x != null);
    const predictStartIndex = Math.min(lastActualIdx + 1, months - 1);

    // 予測（現在→未来）。左側は null で埋める
    const predicted: Series = Array(months).fill(null);
    let base = (actual[lastActualIdx] ?? 12000) as number;
    for (let i = predictStartIndex; i < months; i++) {
        const drift = 120 + Math.floor(rand() * 80);
        const noise = Math.floor((rand() - 0.5) * 300);
        base = Math.max(600, base + drift + noise);
        predicted[i] = base;
    }

    // 過去予測（例として 2 本）
    // 1) 12ヶ月前時点のモデル
    // 2) 24ヶ月前時点のモデル
    const historicalPredictions: HistoricalPrediction[] = [];
    [12, 24].forEach((ago) => {
        const asOfIndex = Math.max(0, predictStartIndex - ago);
        const values: Series = Array(months).fill(null);
        let pastBase = (actual[asOfIndex] ?? 10000) as number;
        for (let i = asOfIndex; i < Math.min(asOfIndex + 18, months); i++) {
            const drift = 90 + Math.floor(rand() * 70);
            const noise = Math.floor((rand() - 0.5) * 320);
            pastBase = Math.max(500, pastBase + drift + noise);
            values[i] = pastBase;
        }
        historicalPredictions.push({ asOfIndex, values });
    });

    return {
        ticker,
        labels,
        actual,
        predicted,
        historicalPredictions,
        predictStartIndex,
        comment: "モック：需給の改善とセクター堅調見通し。為替の追い風を想定。",
    };
}

const SAMPLE_TICKERS = [
  { ticker: "7203.T", name: "TOYOTA" },
  { ticker: "6758.T", name: "SONY" },
  { ticker: "9984.T", name: "SoftBank G" },
  { ticker: "9432.T", name: "NTT" },
  { ticker: "2413.T", name: "M3" },
  { ticker: "8035.T", name: "Tokyo Electron" },
];

export type Mover = {
  ticker: string;
  name?: string;
  changePct: number;
  price?: number;
};

export function makeMockMovers(limit = 5): Mover[] {
  // 適当にダミーの騰落率/価格を合成
  const now = Date.now();
  const pick = SAMPLE_TICKERS
    .map((t, i) => {
      const seed = ((now / 60000) | 0) + i * 97; // 毎分ちょっと入れ替わる
      const rand = Math.sin(seed) * 0.5 + 0.5;   // 0..1
      const changePct = Math.round(((rand * 8 - 4) + (i - 2)) * 10) / 10; // -8%..+8%くらい
      const price = Math.round(5000 + (rand * 15000));
      return { ...t, changePct, price };
    })
    // 絶対値の大きい順（=よく動いている）
    .sort((a, b) => Math.abs(b.changePct) - Math.abs(a.changePct))
    .slice(0, limit);

  return pick;
}