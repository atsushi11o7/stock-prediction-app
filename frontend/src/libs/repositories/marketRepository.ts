import { makeMockMovers } from "@/temp/stockForecast.mock";

export type Mover = {
    ticker: string;       // 例: "7203.T"
    name?: string;        // 任意: 会社名
    changePct: number;    // 24h / 当日騰落率 (%)
    price?: number;       // 現在値（円）
};

export type MarketOverview = {
    date: string;
    totalStocks: number;
    advancing: number;
    declining: number;
    unchanged: number;
    avgChangePct: number;
    topGainer?: {
        ticker: string;
        name: string;
        changePct: number;
    };
    topLoser?: {
        ticker: string;
        name: string;
        changePct: number;
    };
};

/**
 * 大きく動いた銘柄（上位 N 件）。
 * - 本番: /api/market/movers?limit=5
 * - 失敗時: モック
 */
export async function getTopMovers(limit = 5): Promise<Mover[]> {
    try {
        const base = process.env.NEXT_PUBLIC_API_BASE ?? "";
        const res  = await fetch(`${base}/api/market/movers?limit=${limit}`, { cache: "no-store" });
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as Mover[];
        if (!Array.isArray(json)) throw new Error("invalid payload");
        return json.slice(0, limit);
    } catch {
        return makeMockMovers(limit);
    }
}

/**
 * 値上がり銘柄（上位 N 件）。
 * - 本番: /api/market/gainers?limit=10
 * - 失敗時: モック
 */
export async function getGainers(limit = 10): Promise<Mover[]> {
    try {
        const base = process.env.NEXT_PUBLIC_API_BASE ?? "";
        const res  = await fetch(`${base}/api/market/gainers?limit=${limit}`, { cache: "no-store" });
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as Mover[];
        if (!Array.isArray(json)) throw new Error("invalid payload");
        return json.slice(0, limit);
    } catch {
        return makeMockMovers(limit).filter(m => m.changePct > 0);
    }
}

/**
 * 値下がり銘柄（上位 N 件）。
 * - 本番: /api/market/losers?limit=10
 * - 失敗時: モック
 */
export async function getLosers(limit = 10): Promise<Mover[]> {
    try {
        const base = process.env.NEXT_PUBLIC_API_BASE ?? "";
        const res  = await fetch(`${base}/api/market/losers?limit=${limit}`, { cache: "no-store" });
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as Mover[];
        if (!Array.isArray(json)) throw new Error("invalid payload");
        return json.slice(0, limit);
    } catch {
        return makeMockMovers(limit).filter(m => m.changePct < 0);
    }
}

/**
 * 市場全体のサマリー。
 * - 本番: /api/market/overview
 * - 失敗時: モック
 */
export async function getMarketOverview(): Promise<MarketOverview> {
    try {
        const base = process.env.NEXT_PUBLIC_API_BASE ?? "";
        const res  = await fetch(`${base}/api/market/overview`, { cache: "no-store" });
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as MarketOverview;
        return json;
    } catch {
        // モックデータを返す
        return {
            date: new Date().toISOString().split('T')[0],
            totalStocks: 31,
            advancing: 18,
            declining: 11,
            unchanged: 2,
            avgChangePct: 0.52,
            topGainer: {
                ticker: "7203.T",
                name: "トヨタ自動車",
                changePct: 3.45,
            },
            topLoser: {
                ticker: "9984.T",
                name: "ソフトバンクグループ",
                changePct: -2.15,
            },
        };
    }
}