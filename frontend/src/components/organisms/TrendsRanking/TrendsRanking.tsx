"use client";

import { useRouter } from "next/navigation";
import Badge from "@/components/atoms/Badge";
import { formatYen, formatPercent } from "@/libs/utils/formatters";
import type { StockDetail } from "@/libs/repositories/stockRepository";

type Props = {
    stocks: StockDetail[];
    title: string;
    type: "top" | "bottom";
    limit?: number;
};

export default function TrendsRanking({ stocks, title, type, limit = 10 }: Props) {
    const router = useRouter();

    // 予測リターンでソート
    const sortedStocks = [...stocks]
        .filter((s) => s.forecast?.predicted12mReturn != null)
        .sort((a, b) => {
            const aVal = Number(a.forecast?.predicted12mReturn ?? 0);
            const bVal = Number(b.forecast?.predicted12mReturn ?? 0);
            return type === "top" ? bVal - aVal : aVal - bVal;
        })
        .slice(0, limit);

    return (
        <div className="rounded-2xl border border-white/10 bg-[var(--color-surface-1)] overflow-hidden">
            <div className="px-5 py-4 border-b border-white/10 bg-[var(--color-surface-2)]">
                <h3 className="text-lg font-bold text-[var(--color-text-1)]">{title}</h3>
            </div>
            <div className="divide-y divide-white/5">
                {sortedStocks.map((stock, index) => (
                    <div
                        key={stock.ticker}
                        className="flex items-center gap-4 px-5 py-3 hover:bg-[var(--color-surface-2)] transition-colors cursor-pointer"
                        onClick={() => router.push(`/stocks/${stock.ticker}`)}
                    >
                        {/* 順位 */}
                        <div className="w-8 h-8 rounded-full bg-[var(--color-surface-3)] flex items-center justify-center text-sm font-bold text-[var(--color-text-2)]">
                            {index + 1}
                        </div>

                        {/* 銘柄情報 */}
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-[var(--color-text-1)] truncate">
                                    {stock.name}
                                </span>
                                <span className="text-xs text-[var(--color-text-3)]">
                                    {stock.ticker}
                                </span>
                            </div>
                            <div className="text-xs text-[var(--color-text-3)] mt-0.5">
                                {stock.sector}
                            </div>
                        </div>

                        {/* 株価 */}
                        <div className="text-right">
                            <div className="text-sm font-medium text-[var(--color-text-1)]">
                                {formatYen(stock.price)}
                            </div>
                            <Badge
                                tone={stock.changePct >= 0 ? "success" : "danger"}
                                size="sm"
                            >
                                {formatPercent(stock.changePct)}
                            </Badge>
                        </div>

                        {/* 予測リターン */}
                        <div className="w-24 text-right">
                            <div className="text-xs text-[var(--color-text-3)] mb-1">予測</div>
                            <Badge
                                tone={Number(stock.forecast?.predicted12mReturn) >= 0 ? "success" : "danger"}
                                size="sm"
                            >
                                {formatPercent(Number(stock.forecast?.predicted12mReturn))}
                            </Badge>
                        </div>
                    </div>
                ))}
                {sortedStocks.length === 0 && (
                    <div className="px-5 py-8 text-center text-sm text-[var(--color-text-3)]">
                        データがありません
                    </div>
                )}
            </div>
        </div>
    );
}
