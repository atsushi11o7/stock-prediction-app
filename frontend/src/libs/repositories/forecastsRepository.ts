// Forecasts ranking repository

export type ForecastRanking = {
    ticker: string;
    name: string;
    currentPrice: number;
    predicted12mPrice: number;
    predicted12mReturn: number;
};

export type ForecastsLatest = {
    predictedAt: string;
    modelVersion: string;
    forecasts: ForecastRanking[];
};

export type ForecastStatistics = {
    count: number;
    avgReturn: number;
    maxReturn: number;
    minReturn: number;
    medianReturn: number;
};

/**
 * 最新の全予測を取得。
 * - 本番: /api/forecasts/latest
 * - 失敗時: null
 */
export async function getLatestForecasts(): Promise<ForecastsLatest | null> {
    try {
        const base = process.env.NEXT_PUBLIC_API_BASE ?? "";
        const res = await fetch(`${base}/api/forecasts/latest`, {
            cache: "no-store",
        });
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as ForecastsLatest;
        return json;
    } catch {
        return null;
    }
}

/**
 * 高リターン予測のランキングを取得。
 * - 本番: /api/forecasts/top_returns?limit=10
 * - 失敗時: 空配列
 */
export async function getTopReturns(limit = 10): Promise<ForecastRanking[]> {
    try {
        const base = process.env.NEXT_PUBLIC_API_BASE ?? "";
        const res = await fetch(`${base}/api/forecasts/top_returns?limit=${limit}`, {
            cache: "no-store",
        });
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as ForecastRanking[];
        if (!Array.isArray(json)) throw new Error("invalid payload");
        return json;
    } catch {
        return [];
    }
}

/**
 * 低リターン予測のランキングを取得。
 * - 本番: /api/forecasts/bottom_returns?limit=10
 * - 失敗時: 空配列
 */
export async function getBottomReturns(limit = 10): Promise<ForecastRanking[]> {
    try {
        const base = process.env.NEXT_PUBLIC_API_BASE ?? "";
        const res = await fetch(`${base}/api/forecasts/bottom_returns?limit=${limit}`, {
            cache: "no-store",
        });
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as ForecastRanking[];
        if (!Array.isArray(json)) throw new Error("invalid payload");
        return json;
    } catch {
        return [];
    }
}

/**
 * 予測統計を取得。
 * - 本番: /api/forecasts/statistics
 * - 失敗時: null
 */
export async function getForecastStatistics(): Promise<ForecastStatistics | null> {
    try {
        const base = process.env.NEXT_PUBLIC_API_BASE ?? "";
        const res = await fetch(`${base}/api/forecasts/statistics`, {
            cache: "no-store",
        });
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as ForecastStatistics;
        return json;
    } catch {
        return null;
    }
}
