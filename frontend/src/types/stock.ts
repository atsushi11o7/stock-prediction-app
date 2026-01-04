/**
 * 株式関連の共通型定義
 */

/**
 * 株式ティッカー情報
 */
export type StockTicker = {
    ticker: string;
    name: string;
    price: number;
    changePct: number;
};

/**
 * 値動き銘柄情報 (値上がり・値下がり等)
 */
export type Mover = {
    ticker: string;
    name?: string;
    changePct: number;
    price?: number;
};

/**
 * 株式詳細情報
 */
export type StockDetail = {
    ticker: string;
    name: string;
    sector?: string;
    industry?: string;
    price: number;
    changePct: number;
    marketCap?: number;
    volume?: number;
};

/**
 * 市場概況
 */
export type MarketOverview = {
    date: string;
    totalStocks: number;
    advancing: number;
    declining: number;
    unchanged: number;
    avgChangePct: number;
    topGainer?: Mover;
    topLoser?: Mover;
};
