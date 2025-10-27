import { makeMockMovers } from "@/temp/stockForecast.mock";

export type Mover = {
    ticker: string;       // 例: "7203.T"
    name?: string;        // 任意: 会社名
    changePct: number;    // 24h / 当日騰落率 (%)
    price?: number;       // 現在値（円）
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