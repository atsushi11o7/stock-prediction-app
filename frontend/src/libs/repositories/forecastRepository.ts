import type { StockForecastData } from "@/libs/chart/types";
import { makeMockForecast } from "@/temp/stockForecast.mock";

/**
 * 予測データ取得。
 * - 本番：/api/stocks/:ticker/forecast から取得
 * - 404/ネットワーク失敗：モックにフォールバック（ビルド・開発で常に表示可能）
 */
export async function getForecast(ticker: string): Promise<StockForecastData> {
    try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE ?? ""}/api/stocks/${encodeURIComponent(ticker)}/forecast`, {
            // Next.js のサーバーコンポーネント側から呼ぶなら既定のままでOK
            // SPA クライアント側からも呼ぶ場合は CORS 設定を忘れずに
            cache: "no-store",
        });
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as StockForecastData;
        // 簡易検証：最低限のキーがあるか
        if (!json || !json.labels || !json.actual || !json.predicted) throw new Error("invalid payload");
        return json;
    } catch {
        // バックエンド未整備 or 失敗 → モック
        return makeMockForecast(ticker);
    }
}