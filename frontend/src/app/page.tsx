// src/app/page.tsx
import Link from "next/link";

import RightRail from "@/components/organisms/RightRail";
import RailCard from "@/components/molecules/RailCard";
import StockForecastCard from "@/components/organisms/StockForecastCard";
import TickerScroller, { type TickerItem } from "@/components/organisms/TickerScroller";
import { getForecast } from "@/libs/repositories/forecastRepository";
import { getTopMovers } from "@/libs/repositories/marketRepository";

type Mover = {
    ticker: string;
    name?: string;
    price?: number;
    changePct?: number;
};

export default async function Home() {
    // 1) movers を取得（モックフォールバック込み）
    const movers = (await getTopMovers(4)) as Mover[]; // ← any回避のため最低限の型を付与

    // 2) 上位1件を “ピックアップ” として大きめカードに
    const featured = movers[0] ?? { ticker: "7203.T", name: "TOYOTA", changePct: 0 };

    // 3) その銘柄の予測データ（モックフォールバック込み）
    const data = await getForecast(featured.ticker);

    // 4) 残りを右レールや簡易リストに
    const others = movers.slice(1);

    const indices: TickerItem[] = [
        { symbol: "NIKKEI225", name: "日経平均", price: 40123, changePct: 0.52, size: "md" },
        { symbol: "TOPIX", name: "TOPIX", price: 2845.12, changePct: -0.08, size: "md" },
    ];

    const moverItems: TickerItem[] = movers.map((m) => ({
        symbol: m.ticker,
        name: m.name ?? m.ticker,
        price: typeof m.price === "number" ? m.price : 0,          // ← any不使用・型ガード
        changePct: typeof m.changePct === "number" ? m.changePct : 0,
        size: "sm",
    }));

    return (
        <>
            {/* ラッパー: 画面幅に収まるレスポンシブ2カラム */}
            <div className="mx-auto max-w-screen-2xl px-4 lg:grid lg:grid-cols-[minmax(0,1fr)_320px] lg:gap-6">
                {/* メイン領域（min-w-0で内側のはみ出し抑制） */}
                <main className="p-6 min-w-0">
                    <section className="max-w-5xl">
                        <h1 className="text-2xl font-bold">ようこそ FumiKabu へ</h1>
                        <p className="mt-2 text-[var(--color-text-3)]">
                            直近で大きく動いた銘柄をピックアップ。予測と合わせてチェックしましょう。
                        </p>

                        <div className="mt-4">
                            <TickerScroller
                                indices={indices}
                                movers={moverItems}
                                seeAll={{ href: "/stocks", label: "株価一覧へ" }}
                                cardHeight={88}
                            />
                        </div>

                        {/* ピックアップ：上位1銘柄を大きめカードで */}
                        <div className="mt-6">
                            <StockForecastCard
                                data={data}
                                title={`${featured.ticker} Stock Forecast`}
                                subtitle={`${featured.name ?? ""} / Δ ${featured.changePct && featured.changePct > 0 ? "+" : ""}${featured.changePct ?? 0}%`}
                                tag="Today’s mover"
                                metrics={[
                                    { label: "Price",  value: `¥${(others[0]?.price ?? 12840).toLocaleString()}` },
                                    { label: "Change", value: `${featured.changePct && featured.changePct > 0 ? "+" : ""}${featured.changePct ?? 0}%`, tone: (featured.changePct ?? 0) >= 0 ? "up" : "down" },
                                    { label: "PER",    value: "12.7x", tone: "brand" },
                                    { label: "Sector", value: "Automobile" },
                                ]}
                                showLegend
                                chartProps={{
                                    showAxes: true,
                                    xTickMonths: [6, 12],
                                    yTickCount: 5,
                                }}
                            />
                        </div>

                        <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-3">
                            <Link href="/stocks"  className="rounded-2xl border border-white/10 bg-[var(--color-surface-1)] px-4 py-3 hover:bg-[var(--color-surface-2)] transition">銘柄一覧へ</Link>
                            <Link href="/trends"  className="rounded-2xl border border-white/10 bg-[var(--color-surface-1)] px-4 py-3 hover:bg-[var(--color-surface-2)] transition">トレンドを見る</Link>
                            <Link href="/compare" className="rounded-2xl border border-white/10 bg-[var(--color-surface-1)] px-4 py-3 hover:bg-[var(--color-surface-2)] transition">銘柄を比較</Link>
                        </div>
                    </section>
                </main>

                <RightRail>
                    <RailCard title="Market Overview">
                        <ul className="space-y-2 text-sm">
                            <li className="flex justify-between"><span>Nikkei 225</span><span className="text-green-400">+0.8%</span></li>
                            <li className="flex justify-between"><span>S&amp;P 500</span><span className="text-red-400">-0.3%</span></li>
                        </ul>
                    </RailCard>

                    <RailCard title="Top Movers">
                        <ul className="space-y-2 text-sm">
                            <li className="flex justify-between"><span>NVDA</span><span className="text-green-400">+2.1%</span></li>
                            <li className="flex justify-between"><span>TSLA</span><span className="text-red-400">-1.2%</span></li>
                        </ul>
                    </RailCard>

                    <RailCard title="News Digest">
                        <ul className="space-y-2 text-sm">
                            <li className="hover:underline cursor-pointer">BOJ hints at policy shift</li>
                            <li className="hover:underline cursor-pointer">NVIDIA reaches new high</li>
                        </ul>
                    </RailCard>

                    <RailCard title="Quick Tip">
                        <p className="text-[var(--color-text-3)] text-sm">
                            PER = 株価 ÷ 1株あたり利益（EPS）
                        </p>
                    </RailCard>
                </RightRail>
            </div>
        </>
    );
}