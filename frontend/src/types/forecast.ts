/**
 * 予測関連の共通型定義
 */

/**
 * 予測ランキング情報
 */
export type ForecastRanking = {
    ticker: string;
    name?: string;
    predicted12mReturn: number;
    currentPrice: number;
    predictedPrice?: number;
    confidence?: number;
};

/**
 * 最新予測データ
 */
export type ForecastLatest = {
    ticker: string;
    name?: string;
    currentPrice: number;
    predicted12mReturn: number;
    predicted12mPrice?: number;
    confidence?: number;
    updatedAt?: string;
};

/**
 * 予測統計情報
 */
export type ForecastStatistics = {
    totalForecasts: number;
    avgReturn: number;
    maxReturn: number;
    minReturn: number;
    highConfidenceCount: number;
};

/**
 * チャート用予測データ
 */
export type StockForecastData = {
    ticker: string;
    labels: string[];
    actual: (number | null)[];
    predicted: (number | null)[];
    lower?: (number | null)[];
    upper?: (number | null)[];
};
