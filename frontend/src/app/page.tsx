// src/app/page.tsx
import Link from "next/link";

import RightRail from "@/components/organisms/RightRail";
import RailCard from "@/components/molecules/RailCard";
import StockForecastCard from "@/components/organisms/StockForecastCard";
import TickerScroller, { type TickerItem } from "@/components/organisms/TickerScroller";
import StatCard from "@/components/atoms/StatCard";
import Badge from "@/components/atoms/Badge";
import { getForecast } from "@/libs/repositories/forecastRepository";
import { getTopMovers, getMarketOverview, getGainers, getLosers } from "@/libs/repositories/marketRepository";
import { getStockDetail } from "@/libs/repositories/stockRepository";
import { getTopReturns } from "@/libs/repositories/forecastsRepository";

export default async function Home() {
    // 1) 市場サマリーを取得
    const overview = await getMarketOverview();

    // 2) movers を取得（変動が大きい銘柄）
    const movers = await getTopMovers(5);

    // 3) 上位1件を "ピックアップ" として大きめカードに
    const featured = movers[0] ?? { ticker: "7203.T", name: "TOYOTA", changePct: 0, price: 0 };

    // 4) その銘柄の詳細と予測データを取得
    const stockDetail = await getStockDetail(featured.ticker);
    const forecastData = await getForecast(featured.ticker);

    // 5) 値上がり・値下がり銘柄
    const gainers = await getGainers(5);
    const losers = await getLosers(5);

    // 6) 予測ランキング
    const topReturns = await getTopReturns(3);

    // ティッカースクロール用のデータ（注目銘柄予測と重複を除外）
    const moverItems: TickerItem[] = movers
        .filter((m) => m.ticker !== featured.ticker)
        .map((m) => ({
            symbol: m.ticker,
            name: m.name ?? m.ticker,
            price: m.price ?? 0,
            changePct: m.changePct ?? 0,
            size: "sm" as const,
        }));

    return (
        <>
            {/* ラッパー: 画面幅に収まるレスポンシブ2カラム */}
            <div className="mx-auto max-w-screen-2xl px-4">
                {/* メイン領域（min-w-0で内側のはみ出し抑制） */}
                <main className="p-4 md:p-6 lg:p-8 min-w-0 lg:pr-[296px]">
                    <section className="max-w-5xl">
                        {/* ヒーローセクション */}
                        <div className="relative mb-6 p-8 rounded-3xl border border-white/10 bg-[var(--color-surface-1)] overflow-hidden">
                            {/* 装飾的な要素 */}
                            <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--color-brand-500)]/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
                            <div className="absolute bottom-0 left-0 w-48 h-48 bg-[var(--color-brand-500)]/5 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2"></div>

                            <div className="relative">
                                <h1 className="text-3xl md:text-5xl font-bold mb-4 tracking-tight">
                                    ようこそ FumiKabu へ
                                </h1>
                                <p className="text-base md:text-xl text-[var(--color-text-2)] max-w-2xl leading-relaxed">
                                    AIによる株価予測で、あなたの投資判断をサポート。<br className="hidden md:block" />
                                    本日の市場動向と注目銘柄をチェックしましょう。
                                </p>
                            </div>
                        </div>

                        {/* 市場統計サマリー */}
                        <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
                            <StatCard
                                label="全銘柄数"
                                value={overview.totalStocks.toString()}
                                tone="neutral"
                            />
                            <StatCard
                                label="値上がり銘柄"
                                value={overview.advancing.toString()}
                                subvalue={`${((overview.advancing / overview.totalStocks) * 100).toFixed(1)}%`}
                                tone="success"
                            />
                            <StatCard
                                label="値下がり銘柄"
                                value={overview.declining.toString()}
                                subvalue={`${((overview.declining / overview.totalStocks) * 100).toFixed(1)}%`}
                                tone="danger"
                            />
                            <StatCard
                                label="平均変動率"
                                value={`${Number(overview.avgChangePct) > 0 ? '+' : ''}${Number(overview.avgChangePct).toFixed(2)}%`}
                                tone={Number(overview.avgChangePct) >= 0 ? "success" : "danger"}
                            />
                        </div>

                        {/* ピックアップ：上位1銘柄を大きめカードで */}
                        <div className="mt-6">
                            <h2 className="text-xl font-bold mb-4">
                                注目銘柄予測
                            </h2>
                            <StockForecastCard
                                data={forecastData}
                                title={`${featured.ticker} ${featured.name ?? ""}`}
                                subtitle={stockDetail ? `${stockDetail.sector} / ${stockDetail.industry}` : undefined}
                                tag="本日最大の変動"
                                metrics={stockDetail ? [
                                    {
                                        label: "株価",
                                        value: `¥${Number(stockDetail.price).toLocaleString()}`
                                    },
                                    {
                                        label: "変動",
                                        value: `${Number(stockDetail.changePct) > 0 ? '+' : ''}${Number(stockDetail.changePct).toFixed(2)}%`,
                                        tone: Number(stockDetail.changePct) >= 0 ? "up" : "down"
                                    },
                                    {
                                        label: "PER",
                                        value: stockDetail.kpi.per ? `${Number(stockDetail.kpi.per).toFixed(1)}x` : "N/A",
                                        tone: (stockDetail.kpi.per && Number(stockDetail.kpi.per) < 15) ? "brand" : undefined
                                    },
                                    {
                                        label: "配当利回り",
                                        value: stockDetail.kpi.dividendYield ? `${Number(stockDetail.kpi.dividendYield).toFixed(1)}%` : "N/A",
                                        tone: (stockDetail.kpi.dividendYield && Number(stockDetail.kpi.dividendYield) > 3) ? "brand" : undefined
                                    },
                                    {
                                        label: "ROE",
                                        value: stockDetail.kpi.roe ? `${Number(stockDetail.kpi.roe).toFixed(1)}%` : "N/A",
                                        tone: (stockDetail.kpi.roe && Number(stockDetail.kpi.roe) > 10) ? "brand" : undefined
                                    },
                                    {
                                        label: "予測リターン",
                                        value: stockDetail.forecast?.predicted12mReturn
                                            ? `${Number(stockDetail.forecast.predicted12mReturn) > 0 ? '+' : ''}${Number(stockDetail.forecast.predicted12mReturn).toFixed(1)}%`
                                            : "N/A",
                                        tone: (stockDetail.forecast?.predicted12mReturn && Number(stockDetail.forecast.predicted12mReturn) > 0) ? "up" : "down"
                                    },
                                ] : [
                                    { label: "株価", value: `¥${featured.price?.toLocaleString() ?? 'N/A'}` },
                                    { label: "変動", value: `${featured.changePct && featured.changePct > 0 ? '+' : ''}${featured.changePct?.toFixed(2) ?? 0}%`, tone: (featured.changePct ?? 0) >= 0 ? "up" : "down" },
                                ]}
                                showLegend
                                chartProps={{
                                    showAxes: true,
                                    xTickMonths: [6, 12],
                                    yTickCount: 5,
                                }}
                            />
                        </div>

                        <div className="mt-6">
                            <h2 className="text-xl font-bold mb-4">
                                その他の注目株
                            </h2>
                            <TickerScroller
                                indices={[]}
                                movers={moverItems}
                                seeAll={{ href: "/stocks", label: "株価一覧へ" }}
                                cardHeight={88}
                            />
                        </div>

                        {/* 主要機能へのクイックリンク */}
                        <div className="mt-8">
                            <h2 className="text-xl font-bold mb-4">
                                主要機能
                            </h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                                <Link
                                    href="/stocks"
                                    className="group relative overflow-hidden rounded-2xl border border-white/10 bg-[var(--color-surface-1)] p-6 transition-all duration-300 hover:border-[var(--color-brand-500)] hover:shadow-xl hover:shadow-[var(--color-brand-500)]/10 hover:-translate-y-1"
                                >
                                    <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-all duration-300"></div>
                                    <div className="relative">
                                        <div className="w-12 h-12 mb-3 rounded-xl bg-[var(--color-brand-500)]/10 flex items-center justify-center transform group-hover:scale-110 transition-transform duration-300">
                                            <svg className="w-6 h-6 text-[var(--color-brand-500)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                                        </div>
                                        <h3 className="font-bold text-lg mb-2 group-hover:text-[var(--color-brand-500)] transition-colors">銘柄一覧</h3>
                                        <p className="text-sm text-[var(--color-text-3)] leading-relaxed">全銘柄の株価と詳細情報を確認</p>
                                    </div>
                                </Link>
                                <Link
                                    href="/forecasts"
                                    className="group relative overflow-hidden rounded-2xl border border-white/10 bg-[var(--color-surface-1)] p-6 transition-all duration-300 hover:border-[var(--color-brand-500)] hover:shadow-xl hover:shadow-[var(--color-brand-500)]/10 hover:-translate-y-1"
                                >
                                    <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-all duration-300"></div>
                                    <div className="relative">
                                        <div className="w-12 h-12 mb-3 rounded-xl bg-[var(--color-brand-500)]/10 flex items-center justify-center transform group-hover:scale-110 transition-transform duration-300">
                                            <svg className="w-6 h-6 text-[var(--color-brand-500)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                                        </div>
                                        <h3 className="font-bold text-lg mb-2 group-hover:text-[var(--color-brand-500)] transition-colors">予測ランキング</h3>
                                        <p className="text-sm text-[var(--color-text-3)] leading-relaxed">AI予測による期待リターン順</p>
                                    </div>
                                </Link>
                                <Link
                                    href="/screening"
                                    className="group relative overflow-hidden rounded-2xl border border-white/10 bg-[var(--color-surface-1)] p-6 transition-all duration-300 hover:border-[var(--color-brand-500)] hover:shadow-xl hover:shadow-[var(--color-brand-500)]/10 hover:-translate-y-1"
                                >
                                    <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-all duration-300"></div>
                                    <div className="relative">
                                        <div className="w-12 h-12 mb-3 rounded-xl bg-[var(--color-brand-500)]/10 flex items-center justify-center transform group-hover:scale-110 transition-transform duration-300">
                                            <svg className="w-6 h-6 text-[var(--color-brand-500)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
                                        </div>
                                        <h3 className="font-bold text-lg mb-2 group-hover:text-[var(--color-brand-500)] transition-colors">スクリーニング</h3>
                                        <p className="text-sm text-[var(--color-text-3)] leading-relaxed">条件を指定して銘柄を絞り込み</p>
                                    </div>
                                </Link>
                            </div>
                        </div>

                        {/* AI予測の特徴セクション */}
                        <div className="mt-8">
                            <h2 className="text-xl font-bold mb-4">
                                AI予測の特徴
                            </h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                <div className="group relative overflow-hidden rounded-2xl border border-white/10 bg-[var(--color-surface-1)] p-7 transition-all duration-300 hover:border-[var(--color-brand-500)]/30 hover:shadow-xl hover:shadow-[var(--color-brand-500)]/10">
                                    <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-all duration-300"></div>
                                    <div className="relative flex items-start gap-4">
                                        <div className="shrink-0 w-12 h-12 rounded-xl bg-[var(--color-brand-500)]/10 flex items-center justify-center transform group-hover:scale-110 transition-transform duration-300">
                                            <svg className="w-6 h-6 text-[var(--color-brand-500)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-lg mb-2 group-hover:text-[var(--color-brand-500)] transition-colors">高精度AI予測</h3>
                                            <p className="text-sm text-[var(--color-text-3)] leading-relaxed">
                                                機械学習モデルによる12ヶ月先の株価予測。過去のデータから学習し、未来のトレンドを予測します。
                                            </p>
                                        </div>
                                    </div>
                                </div>
                                <div className="group relative overflow-hidden rounded-2xl border border-white/10 bg-[var(--color-surface-1)] p-7 transition-all duration-300 hover:border-[var(--color-brand-500)]/30 hover:shadow-xl hover:shadow-[var(--color-brand-500)]/10">
                                    <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-all duration-300"></div>
                                    <div className="relative flex items-start gap-4">
                                        <div className="shrink-0 w-12 h-12 rounded-xl bg-[var(--color-brand-500)]/10 flex items-center justify-center transform group-hover:scale-110 transition-transform duration-300">
                                            <svg className="w-6 h-6 text-[var(--color-brand-500)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-lg mb-2 group-hover:text-[var(--color-brand-500)] transition-colors">リアルタイム分析</h3>
                                            <p className="text-sm text-[var(--color-text-3)] leading-relaxed">
                                                市場データを常に監視し、最新の情報に基づいた投資判断をサポートします。
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>
                </main>

                {/* RightRail: デスクトップでは固定位置、タブレット以下ではmainの下に表示 */}
                <RightRail
                    paddingClass="px-4 py-5"
                    className="lg:fixed lg:top-0 lg:right-0 lg:h-screen lg:w-[280px] lg:overflow-y-auto"
                >
                    {/* 高リターン予測 TOP3 */}
                    <RailCard title="高リターン予測 TOP3">
                        {topReturns.length > 0 ? (
                            <>
                                <ul className="space-y-2">
                                    {topReturns.map((f, i) => (
                                        <li key={f.ticker} className="group flex items-start gap-2 p-3 rounded-xl hover:bg-[var(--color-surface-3)]/50 transition-colors duration-200">
                                            <span className="text-[var(--color-brand-500)] font-bold text-sm mt-0.5">
                                                {i + 1}.
                                            </span>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex justify-between items-baseline gap-2">
                                                    <Link
                                                        href={`/stocks/${f.ticker}`}
                                                        className="truncate text-sm font-semibold group-hover:text-[var(--color-brand-500)] transition-colors"
                                                    >
                                                        {f.name}
                                                    </Link>
                                                    <Badge tone="success" size="sm">
                                                        +{Number(f.predicted12mReturn).toFixed(1)}%
                                                    </Badge>
                                                </div>
                                                <p className="text-xs text-[var(--color-text-3)] mt-0.5">
                                                    {f.ticker} • ¥{Number(f.currentPrice).toLocaleString()}
                                                </p>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                                <Link
                                    href="/forecasts"
                                    className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-[var(--color-brand-500)] hover:gap-2 transition-all duration-200"
                                >
                                    すべての予測を見る
                                    <span className="text-sm">→</span>
                                </Link>
                            </>
                        ) : (
                            <p className="text-sm text-[var(--color-text-3)]">データを取得中...</p>
                        )}
                    </RailCard>

                    {/* 市場サマリー */}
                    <RailCard title="市場サマリー">
                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between items-baseline mb-3">
                                    <span className="text-sm font-semibold">本日の騰落</span>
                                    <span className="text-xs text-[var(--color-text-3)]">
                                        {overview.date}
                                    </span>
                                </div>
                                <div className="grid grid-cols-3 gap-3 text-xs">
                                    <div className="text-center p-2 rounded-lg bg-[var(--color-surface-3)]/30 hover:bg-[var(--color-surface-3)]/50 transition-colors">
                                        <div className="text-[var(--color-text-3)] text-[10px] uppercase tracking-wide mb-1">上昇</div>
                                        <div className="text-[var(--color-success)] font-bold text-base">{overview.advancing}</div>
                                    </div>
                                    <div className="text-center p-2 rounded-lg bg-[var(--color-surface-3)]/30 hover:bg-[var(--color-surface-3)]/50 transition-colors">
                                        <div className="text-[var(--color-text-3)] text-[10px] uppercase tracking-wide mb-1">下落</div>
                                        <div className="text-[var(--color-danger)] font-bold text-base">{overview.declining}</div>
                                    </div>
                                    <div className="text-center p-2 rounded-lg bg-[var(--color-surface-3)]/30 hover:bg-[var(--color-surface-3)]/50 transition-colors">
                                        <div className="text-[var(--color-text-3)] text-[10px] uppercase tracking-wide mb-1">変わらず</div>
                                        <div className="text-[var(--color-text-2)] font-bold text-base">{overview.unchanged}</div>
                                    </div>
                                </div>
                            </div>
                            {overview.topGainer && (
                                <div className="pt-3 border-t border-white/10 hover:bg-[var(--color-surface-3)]/30 p-2 rounded-lg -m-2 transition-colors">
                                    <div className="text-xs text-[var(--color-text-3)] mb-2 uppercase tracking-wide font-semibold">トップゲイナー</div>
                                    <div className="flex justify-between items-baseline">
                                        <span className="text-sm font-medium truncate">{overview.topGainer.name}</span>
                                        <span className="text-[var(--color-success)] font-bold ml-2">
                                            +{Number(overview.topGainer.changePct).toFixed(2)}%
                                        </span>
                                    </div>
                                </div>
                            )}
                            {overview.topLoser && (
                                <div className="pt-3 border-t border-white/10 hover:bg-[var(--color-surface-3)]/30 p-2 rounded-lg -m-2 transition-colors">
                                    <div className="text-xs text-[var(--color-text-3)] mb-2 uppercase tracking-wide font-semibold">トップルーザー</div>
                                    <div className="flex justify-between items-baseline">
                                        <span className="text-sm font-medium truncate">{overview.topLoser.name}</span>
                                        <span className="text-[var(--color-danger)] font-bold ml-2">
                                            {Number(overview.topLoser.changePct).toFixed(2)}%
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </RailCard>

                    {/* 本日の値上がり */}
                    <RailCard title="本日の値上がり">
                        {gainers.length > 0 ? (
                            <ul className="space-y-2">
                                {gainers.map((stock) => (
                                    <li key={stock.ticker} className="flex justify-between text-sm">
                                        <Link
                                            href={`/stocks/${stock.ticker}`}
                                            className="truncate hover:underline flex-1 min-w-0"
                                        >
                                            {stock.name ?? stock.ticker}
                                        </Link>
                                        <span className="text-[var(--color-success)] font-medium shrink-0 ml-2">
                                            +{Number(stock.changePct).toFixed(2)}%
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-sm text-[var(--color-text-3)]">データなし</p>
                        )}
                    </RailCard>

                    {/* 本日の値下がり */}
                    <RailCard title="本日の値下がり">
                        {losers.length > 0 ? (
                            <ul className="space-y-2">
                                {losers.map((stock) => (
                                    <li key={stock.ticker} className="flex justify-between text-sm">
                                        <Link
                                            href={`/stocks/${stock.ticker}`}
                                            className="truncate hover:underline flex-1 min-w-0"
                                        >
                                            {stock.name ?? stock.ticker}
                                        </Link>
                                        <span className="text-[var(--color-danger)] font-medium shrink-0 ml-2">
                                            {Number(stock.changePct).toFixed(2)}%
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-sm text-[var(--color-text-3)]">データなし</p>
                        )}
                    </RailCard>
                </RightRail>
            </div>
        </>
    );
}
