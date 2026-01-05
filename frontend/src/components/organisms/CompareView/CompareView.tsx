"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import Badge from "@/components/atoms/Badge";
import { formatYen, formatPercent } from "@/libs/utils/formatters";
import type { StockDetail } from "@/libs/repositories/stockRepository";

type Props = {
    stocks: StockDetail[];
    initialTickers?: string[];
};

export default function CompareView({ stocks, initialTickers = [] }: Props) {
    const router = useRouter();
    const [selectedTickers, setSelectedTickers] = useState<string[]>(initialTickers);
    const [searchTerm, setSearchTerm] = useState("");

    // 選択された銘柄のデータ
    const selectedStocks = useMemo(() => {
        return selectedTickers
            .map((ticker) => stocks.find((s) => s.ticker === ticker))
            .filter((s): s is StockDetail => s !== undefined);
    }, [stocks, selectedTickers]);

    // 検索結果
    const searchResults = useMemo(() => {
        if (!searchTerm) return [];
        const term = searchTerm.toLowerCase();
        return stocks
            .filter(
                (s) =>
                    !selectedTickers.includes(s.ticker) &&
                    (s.ticker.toLowerCase().includes(term) ||
                        s.code.toLowerCase().includes(term) ||
                        s.name.toLowerCase().includes(term))
            )
            .slice(0, 5);
    }, [stocks, searchTerm, selectedTickers]);

    const addStock = (ticker: string) => {
        if (selectedTickers.length >= 4) return;
        setSelectedTickers([...selectedTickers, ticker]);
        setSearchTerm("");
        // URLを更新
        const newTickers = [...selectedTickers, ticker];
        router.replace(`/compare?tickers=${newTickers.join(",")}`);
    };

    const removeStock = (ticker: string) => {
        const newTickers = selectedTickers.filter((t) => t !== ticker);
        setSelectedTickers(newTickers);
        if (newTickers.length > 0) {
            router.replace(`/compare?tickers=${newTickers.join(",")}`);
        } else {
            router.replace("/compare");
        }
    };

    const metrics = [
        { key: "price", label: "株価", format: (s: StockDetail) => formatYen(s.price) },
        {
            key: "changePct",
            label: "変動率",
            format: (s: StockDetail) => formatPercent(s.changePct),
            isBadge: true,
            tone: (s: StockDetail): "success" | "danger" => s.changePct >= 0 ? "success" : "danger",
        },
        {
            key: "predicted",
            label: "予測リターン",
            format: (s: StockDetail) =>
                s.forecast?.predicted12mReturn != null
                    ? formatPercent(Number(s.forecast.predicted12mReturn))
                    : "N/A",
            isBadge: true,
            tone: (s: StockDetail): "success" | "danger" =>
                Number(s.forecast?.predicted12mReturn) >= 0 ? "success" : "danger",
        },
        { key: "per", label: "PER", format: (s: StockDetail) => (s.kpi?.per ? `${s.kpi.per.toFixed(2)}x` : "N/A") },
        { key: "pbr", label: "PBR", format: (s: StockDetail) => (s.kpi?.pbr ? `${s.kpi.pbr.toFixed(2)}x` : "N/A") },
        {
            key: "dividendYield",
            label: "配当利回り",
            format: (s: StockDetail) => (s.kpi?.dividendYield ? `${s.kpi.dividendYield.toFixed(2)}%` : "N/A"),
        },
        { key: "roe", label: "ROE", format: (s: StockDetail) => (s.kpi?.roe ? `${s.kpi.roe.toFixed(2)}%` : "N/A") },
        { key: "sector", label: "セクター", format: (s: StockDetail) => s.sector || "N/A" },
        { key: "industry", label: "業種", format: (s: StockDetail) => s.industry || "N/A" },
    ];

    return (
        <div className="space-y-6">
            {/* 銘柄追加セクション */}
            <div className="rounded-2xl border border-white/10 bg-[var(--color-surface-1)] p-5">
                <h3 className="text-lg font-bold text-[var(--color-text-1)] mb-4">
                    比較する銘柄を選択（最大4銘柄）
                </h3>

                {/* 検索入力 */}
                <div className="relative mb-4">
                    <input
                        type="text"
                        placeholder="銘柄コード、名前で検索..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        disabled={selectedTickers.length >= 4}
                        className="w-full px-4 py-3 rounded-xl border border-white/10 bg-[var(--color-surface-2)] text-[var(--color-text-1)] placeholder:text-[var(--color-text-3)] focus:outline-none focus:border-[var(--color-brand-500)] transition-colors disabled:opacity-50"
                    />

                    {/* 検索結果ドロップダウン */}
                    {searchResults.length > 0 && (
                        <div className="absolute top-full left-0 right-0 mt-2 rounded-xl border border-white/10 bg-[var(--color-surface-2)] shadow-xl z-10 overflow-hidden">
                            {searchResults.map((stock) => (
                                <button
                                    key={stock.ticker}
                                    onClick={() => addStock(stock.ticker)}
                                    className="w-full px-4 py-3 text-left hover:bg-[var(--color-surface-3)] transition-colors flex items-center justify-between"
                                >
                                    <div>
                                        <span className="text-sm font-medium text-[var(--color-text-1)]">
                                            {stock.name}
                                        </span>
                                        <span className="text-xs text-[var(--color-text-3)] ml-2">
                                            {stock.ticker}
                                        </span>
                                    </div>
                                    <span className="text-xs text-[var(--color-text-3)]">{stock.sector}</span>
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* 選択済み銘柄 */}
                <div className="flex flex-wrap gap-2">
                    {selectedStocks.map((stock) => (
                        <div
                            key={stock.ticker}
                            className="inline-flex items-center gap-2 px-3 py-2 rounded-full bg-[var(--color-brand-600)] text-white text-sm"
                        >
                            <span>{stock.name}</span>
                            <button
                                onClick={() => removeStock(stock.ticker)}
                                className="w-5 h-5 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center transition-colors"
                            >
                                ✕
                            </button>
                        </div>
                    ))}
                    {selectedTickers.length === 0 && (
                        <span className="text-sm text-[var(--color-text-3)]">
                            銘柄を検索して追加してください
                        </span>
                    )}
                </div>
            </div>

            {/* 比較テーブル */}
            {selectedStocks.length > 0 && (
                <div className="rounded-2xl border border-white/10 bg-[var(--color-surface-1)] overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-[var(--color-surface-2)] border-b border-white/10">
                                <tr>
                                    <th className="px-5 py-4 text-left text-sm font-semibold text-[var(--color-text-2)] w-32">
                                        指標
                                    </th>
                                    {selectedStocks.map((stock) => (
                                        <th
                                            key={stock.ticker}
                                            className="px-5 py-4 text-center text-sm font-semibold text-[var(--color-text-1)] min-w-[140px] cursor-pointer hover:text-[var(--color-brand-500)] transition-colors"
                                            onClick={() => router.push(`/stocks/${stock.ticker}`)}
                                        >
                                            <div>{stock.name}</div>
                                            <div className="text-xs text-[var(--color-text-3)] font-normal mt-0.5">
                                                {stock.ticker}
                                            </div>
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {metrics.map((metric, index) => (
                                    <tr
                                        key={metric.key}
                                        className={index % 2 === 0 ? "bg-[var(--color-surface-1)]" : "bg-[var(--color-surface-2)]/50"}
                                    >
                                        <td className="px-5 py-3 text-sm font-medium text-[var(--color-text-2)]">
                                            {metric.label}
                                        </td>
                                        {selectedStocks.map((stock) => (
                                            <td key={stock.ticker} className="px-5 py-3 text-center">
                                                {metric.isBadge && metric.tone ? (
                                                    <Badge tone={metric.tone(stock)} size="sm">
                                                        {metric.format(stock)}
                                                    </Badge>
                                                ) : (
                                                    <span className="text-sm text-[var(--color-text-1)]">
                                                        {metric.format(stock)}
                                                    </span>
                                                )}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* 空の状態 */}
            {selectedStocks.length === 0 && (
                <div className="rounded-2xl border border-white/10 bg-[var(--color-surface-1)] p-12 text-center">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--color-brand-500)]/10 flex items-center justify-center">
                        <svg className="w-8 h-8 text-[var(--color-brand-500)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-bold text-[var(--color-text-1)] mb-2">
                        銘柄を比較しましょう
                    </h3>
                    <p className="text-sm text-[var(--color-text-3)]">
                        上の検索ボックスから銘柄を追加して、KPIや予測リターンを比較できます
                    </p>
                </div>
            )}
        </div>
    );
}
