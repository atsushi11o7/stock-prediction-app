"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import Badge from "@/components/atoms/Badge";
import { formatPercent } from "@/libs/utils/formatters";
import type { StockDetail } from "@/libs/repositories/stockRepository";

type Props = {
    stocks: StockDetail[];
};

type SectorData = {
    name: string;
    avgReturn: number;
    avgChangePct: number;
    stockCount: number;
};

export default function SectorPerformance({ stocks }: Props) {
    const router = useRouter();

    const sectorData = useMemo(() => {
        const sectorMap = new Map<string, { returns: number[]; changes: number[] }>();

        stocks.forEach((stock) => {
            if (!stock.sector) return;
            const data = sectorMap.get(stock.sector) ?? { returns: [], changes: [] };

            if (stock.forecast?.predicted12mReturn != null) {
                data.returns.push(Number(stock.forecast.predicted12mReturn));
            }
            if (stock.changePct != null) {
                data.changes.push(stock.changePct);
            }

            sectorMap.set(stock.sector, data);
        });

        const result: SectorData[] = [];
        sectorMap.forEach((data, name) => {
            if (data.returns.length === 0) return;
            const avgReturn = data.returns.reduce((a, b) => a + b, 0) / data.returns.length;
            const avgChangePct = data.changes.length > 0
                ? data.changes.reduce((a, b) => a + b, 0) / data.changes.length
                : 0;
            result.push({
                name,
                avgReturn,
                avgChangePct,
                stockCount: data.returns.length,
            });
        });

        return result.sort((a, b) => b.avgReturn - a.avgReturn);
    }, [stocks]);

    return (
        <div className="rounded-2xl border border-white/10 bg-[var(--color-surface-1)] overflow-hidden">
            <div className="px-5 py-4 border-b border-white/10 bg-[var(--color-surface-2)]">
                <h3 className="text-lg font-bold text-[var(--color-text-1)]">セクター別パフォーマンス</h3>
                <p className="text-xs text-[var(--color-text-3)] mt-1">各セクターの平均予測リターン</p>
            </div>
            <div className="divide-y divide-white/5">
                {sectorData.map((sector, index) => (
                    <div
                        key={sector.name}
                        className="flex items-center gap-4 px-5 py-3 hover:bg-[var(--color-surface-2)] transition-colors cursor-pointer"
                        onClick={() => router.push(`/stocks?q=${encodeURIComponent(sector.name)}`)}
                    >
                        {/* 順位 */}
                        <div className="w-8 h-8 rounded-full bg-[var(--color-surface-3)] flex items-center justify-center text-sm font-bold text-[var(--color-text-2)]">
                            {index + 1}
                        </div>

                        {/* セクター情報 */}
                        <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-[var(--color-text-1)]">
                                {sector.name}
                            </div>
                            <div className="text-xs text-[var(--color-text-3)] mt-0.5">
                                {sector.stockCount}銘柄
                            </div>
                        </div>

                        {/* 平均変動率 */}
                        <div className="text-right">
                            <div className="text-xs text-[var(--color-text-3)] mb-1">平均変動率</div>
                            <Badge
                                tone={sector.avgChangePct >= 0 ? "success" : "danger"}
                                size="sm"
                            >
                                {formatPercent(sector.avgChangePct)}
                            </Badge>
                        </div>

                        {/* 平均予測リターン */}
                        <div className="w-28 text-right">
                            <div className="text-xs text-[var(--color-text-3)] mb-1">平均予測</div>
                            <Badge
                                tone={sector.avgReturn >= 0 ? "success" : "danger"}
                                size="sm"
                            >
                                {formatPercent(sector.avgReturn)}
                            </Badge>
                        </div>
                    </div>
                ))}
                {sectorData.length === 0 && (
                    <div className="px-5 py-8 text-center text-sm text-[var(--color-text-3)]">
                        データがありません
                    </div>
                )}
            </div>
        </div>
    );
}
