import TrendsRanking from "@/components/organisms/TrendsRanking";
import SectorPerformance from "@/components/organisms/SectorPerformance";
import { getAllStocks } from "@/libs/repositories/stockRepository";

export default async function TrendsPage() {
    const stocks = await getAllStocks();

    return (
        <div className="mx-auto max-w-screen-2xl px-4">
            <main className="p-4 md:p-6 lg:p-8 min-w-0">
                <section className="max-w-6xl mx-auto">
                    {/* ページヘッダー */}
                    <div className="mb-6">
                        <h1 className="text-3xl md:text-4xl font-bold mb-2 tracking-tight">
                            トレンド
                        </h1>
                        <p className="text-base text-[var(--color-text-2)]">
                            AI予測リターンに基づく銘柄ランキングとセクター別パフォーマンスを表示します。
                        </p>
                    </div>

                    {/* メインコンテンツ */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* 予測リターンTOP10 */}
                        <TrendsRanking
                            stocks={stocks}
                            title="予測リターン TOP10"
                            type="top"
                            limit={10}
                        />

                        {/* 予測リターンWORST10 */}
                        <TrendsRanking
                            stocks={stocks}
                            title="予測リターン WORST10"
                            type="bottom"
                            limit={10}
                        />
                    </div>

                    {/* セクター別パフォーマンス */}
                    <div className="mt-6">
                        <SectorPerformance stocks={stocks} />
                    </div>
                </section>
            </main>
        </div>
    );
}
