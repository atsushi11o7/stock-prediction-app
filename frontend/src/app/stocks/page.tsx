import StocksTable from "@/components/organisms/StocksTable";
import { getAllStocks } from "@/libs/repositories/stockRepository";

export default async function StocksPage() {
    const stocks = await getAllStocks();

    return (
        <div className="mx-auto max-w-screen-2xl px-4">
            <main className="p-4 md:p-6 lg:p-8 min-w-0">
                <section className="max-w-7xl mx-auto">
                    {/* ページヘッダー */}
                    <div className="mb-6">
                        <h1 className="text-3xl md:text-4xl font-bold mb-2 tracking-tight">
                            銘柄一覧
                        </h1>
                        <p className="text-base text-[var(--color-text-2)]">
                            全銘柄の株価、KPI、AI予測リターンを一覧表示します。カラムをクリックしてソート、検索バーで絞り込みができます。
                        </p>
                    </div>

                    {/* 銘柄テーブル */}
                    <StocksTable stocks={stocks} />
                </section>
            </main>
        </div>
    );
}
