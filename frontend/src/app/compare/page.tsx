import CompareView from "@/components/organisms/CompareView";
import { getAllStocks } from "@/libs/repositories/stockRepository";

type Props = {
    searchParams: Promise<{ tickers?: string }>;
};

export default async function ComparePage({ searchParams }: Props) {
    const { tickers } = await searchParams;
    const stocks = await getAllStocks();

    // URLから初期選択銘柄を取得
    const initialTickers = tickers ? tickers.split(",").filter(Boolean) : [];

    return (
        <div className="mx-auto max-w-screen-2xl px-4">
            <main className="p-4 md:p-6 lg:p-8 min-w-0">
                <section className="max-w-6xl mx-auto">
                    {/* ページヘッダー */}
                    <div className="mb-6">
                        <h1 className="text-3xl md:text-4xl font-bold mb-2 tracking-tight">
                            銘柄比較
                        </h1>
                        <p className="text-base text-[var(--color-text-2)]">
                            複数の銘柄を並べて比較できます。株価、KPI、AI予測リターンを一目で確認しましょう。
                        </p>
                    </div>

                    {/* 比較ビュー */}
                    <CompareView stocks={stocks} initialTickers={initialTickers} />
                </section>
            </main>
        </div>
    );
}
