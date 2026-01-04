// Stock detail data repository

export type StockDetail = {
    ticker: string;
    code: string;
    name: string;
    sector: string;
    industry: string;
    price: number;
    changePct: number;
    kpi: {
        per?: number;
        pbr?: number;
        dividendYield?: number;
        marketCap?: number;
        roe?: number;
        roa?: number;
    };
    forecast?: {
        predicted12mReturn?: number;
    };
};

/**
 * 銘柄詳細を取得。
 * - 本番: /api/stocks/:ticker
 * - 失敗時: null
 */
export async function getStockDetail(ticker: string): Promise<StockDetail | null> {
    try {
        const base = process.env.NEXT_PUBLIC_API_BASE ?? "";
        const res = await fetch(`${base}/api/stocks/${encodeURIComponent(ticker)}`, {
            cache: "no-store",
        });
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as StockDetail;
        return json;
    } catch {
        return null;
    }
}

/**
 * 全銘柄リストを取得。
 * - 本番: /api/stocks
 * - 失敗時: 空配列
 */
export async function getAllStocks(): Promise<StockDetail[]> {
    try {
        const base = process.env.NEXT_PUBLIC_API_BASE ?? "";
        const res = await fetch(`${base}/api/stocks`, {
            cache: "no-store",
        });
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as StockDetail[];
        if (!Array.isArray(json)) throw new Error("invalid payload");
        return json;
    } catch {
        return [];
    }
}
