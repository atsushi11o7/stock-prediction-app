import Link from "next/link";
import { notFound } from "next/navigation";
import StockForecastCard from "@/components/organisms/StockForecastCard";
import Badge from "@/components/atoms/Badge";
import { getStockDetail } from "@/libs/repositories/stockRepository";
import { getForecast } from "@/libs/repositories/forecastRepository";
import { formatYen, formatPercent } from "@/libs/utils/formatters";

type Props = {
    params: Promise<{ ticker: string }>;
};

export default async function StockDetailPage({ params }: Props) {
    const { ticker } = await params;
    const decodedTicker = decodeURIComponent(ticker);

    // 銘柄詳細と予測データを並行取得
    const [stockDetail, forecastData] = await Promise.all([
        getStockDetail(decodedTicker),
        getForecast(decodedTicker),
    ]);

    if (!stockDetail) {
        notFound();
    }

    const kpiItems = [
        { label: "PER", value: stockDetail.kpi?.per, format: (v: number) => `${v.toFixed(2)}x` },
        { label: "PBR", value: stockDetail.kpi?.pbr, format: (v: number) => `${v.toFixed(2)}x` },
        { label: "配当利回り", value: stockDetail.kpi?.dividendYield, format: (v: number) => `${v.toFixed(2)}%` },
        { label: "ROE", value: stockDetail.kpi?.roe, format: (v: number) => `${v.toFixed(2)}%` },
        { label: "時価総額", value: stockDetail.kpi?.marketCap, format: (v: number) => `${(v / 1e12).toFixed(2)}兆円` },
    ];

    return (
        <div className="mx-auto max-w-screen-2xl px-4">
            <main className="p-4 md:p-6 lg:p-8 min-w-0">
                <section className="max-w-5xl mx-auto">
                    {/* パンくずリスト */}
                    <nav className="mb-4 text-sm">
                        <ol className="flex items-center gap-2 text-[var(--color-text-3)]">
                            <li>
                                <Link href="/" className="hover:text-[var(--color-brand-500)] transition-colors">
                                    ホーム
                                </Link>
                            </li>
                            <li>/</li>
                            <li>
                                <Link href="/stocks" className="hover:text-[var(--color-brand-500)] transition-colors">
                                    銘柄一覧
                                </Link>
                            </li>
                            <li>/</li>
                            <li className="text-[var(--color-text-1)]">{stockDetail.name}</li>
                        </ol>
                    </nav>

                    {/* ヘッダー */}
                    <div className="mb-6">
                        <div className="flex flex-wrap items-center gap-3 mb-2">
                            <h1 className="text-2xl md:text-3xl font-bold">
                                {stockDetail.name}
                            </h1>
                            <span className="text-lg text-[var(--color-text-2)]">
                                {stockDetail.ticker}
                            </span>
                        </div>
                        <p className="text-sm text-[var(--color-text-3)]">
                            {stockDetail.sector} / {stockDetail.industry}
                        </p>
                    </div>

                    {/* 株価情報カード */}
                    <div className="mb-6 p-6 rounded-2xl border border-white/10 bg-[var(--color-surface-1)]">
                        <div className="flex flex-wrap items-end gap-6">
                            <div>
                                <div className="text-sm text-[var(--color-text-3)] mb-1">現在株価</div>
                                <div className="text-3xl md:text-4xl font-bold">
                                    {formatYen(stockDetail.price)}
                                </div>
                            </div>
                            <div>
                                <div className="text-sm text-[var(--color-text-3)] mb-1">前日比</div>
                                <Badge
                                    tone={stockDetail.changePct >= 0 ? "success" : "danger"}
                                    size="lg"
                                >
                                    {formatPercent(stockDetail.changePct)}
                                </Badge>
                            </div>
                            {stockDetail.forecast?.predicted12mReturn !== undefined && (
                                <div>
                                    <div className="text-sm text-[var(--color-text-3)] mb-1">12ヶ月予測リターン</div>
                                    <Badge
                                        tone={Number(stockDetail.forecast.predicted12mReturn) >= 0 ? "success" : "danger"}
                                        size="lg"
                                    >
                                        {Number(stockDetail.forecast.predicted12mReturn) > 0 ? "+" : ""}
                                        {Number(stockDetail.forecast.predicted12mReturn).toFixed(1)}%
                                    </Badge>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* KPI一覧 */}
                    <div className="mb-6">
                        <h2 className="text-xl font-bold mb-4">主要指標</h2>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                            {kpiItems.map((item) => (
                                <div
                                    key={item.label}
                                    className="p-4 rounded-xl border border-white/10 bg-[var(--color-surface-1)]"
                                >
                                    <div className="text-xs text-[var(--color-text-3)] mb-1">{item.label}</div>
                                    <div className="text-lg font-semibold text-[var(--color-text-1)]">
                                        {item.value != null ? item.format(item.value) : "N/A"}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* 予測チャート */}
                    <div className="mb-6">
                        <h2 className="text-xl font-bold mb-4">株価予測チャート</h2>
                        {forecastData ? (
                            <StockForecastCard
                                data={forecastData}
                                title={`${stockDetail.ticker} ${stockDetail.name}`}
                                showLegend
                                chartProps={{
                                    showAxes: true,
                                    xTickMonths: [6, 12],
                                    yTickCount: 5,
                                }}
                            />
                        ) : (
                            <div className="p-8 rounded-2xl border border-white/10 bg-[var(--color-surface-1)] text-center text-[var(--color-text-3)]">
                                予測データがありません
                            </div>
                        )}
                    </div>

                    {/* 戻るリンク */}
                    <div className="mt-8">
                        <Link
                            href="/stocks"
                            className="inline-flex items-center gap-2 text-sm text-[var(--color-brand-500)] hover:underline"
                        >
                            ← 銘柄一覧に戻る
                        </Link>
                    </div>
                </section>
            </main>
        </div>
    );
}
