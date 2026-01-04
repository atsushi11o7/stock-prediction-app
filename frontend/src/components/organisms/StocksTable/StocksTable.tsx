"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import Badge from "@/components/atoms/Badge";
import { formatYen, formatPercent } from "@/libs/utils/formatters";
import type { StockDetail } from "@/libs/repositories/stockRepository";

type SortKey = "ticker" | "name" | "price" | "changePct" | "per" | "pbr" | "dividendYield" | "predicted12mReturn";
type SortOrder = "asc" | "desc";

type Props = {
    stocks: StockDetail[];
};

export default function StocksTable({ stocks }: Props) {
    const [searchTerm, setSearchTerm] = useState("");
    const [sortKey, setSortKey] = useState<SortKey>("changePct");
    const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

    // ソート処理
    const handleSort = (key: SortKey) => {
        if (sortKey === key) {
            setSortOrder(sortOrder === "asc" ? "desc" : "asc");
        } else {
            setSortKey(key);
            setSortOrder("desc");
        }
    };

    // フィルタ＆ソート
    const filteredAndSortedStocks = useMemo(() => {
        let result = [...stocks];

        // 検索フィルタ
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            result = result.filter(
                (stock) =>
                    stock.ticker.toLowerCase().includes(term) ||
                    stock.code.toLowerCase().includes(term) ||
                    stock.name.toLowerCase().includes(term) ||
                    stock.sector.toLowerCase().includes(term) ||
                    stock.industry.toLowerCase().includes(term)
            );
        }

        // ソート
        result.sort((a, b) => {
            let aVal: number | string | undefined;
            let bVal: number | string | undefined;

            switch (sortKey) {
                case "ticker":
                    aVal = a.ticker;
                    bVal = b.ticker;
                    break;
                case "name":
                    aVal = a.name;
                    bVal = b.name;
                    break;
                case "price":
                    aVal = a.price;
                    bVal = b.price;
                    break;
                case "changePct":
                    aVal = a.changePct;
                    bVal = b.changePct;
                    break;
                case "per":
                    aVal = a.kpi?.per ?? -Infinity;
                    bVal = b.kpi?.per ?? -Infinity;
                    break;
                case "pbr":
                    aVal = a.kpi?.pbr ?? -Infinity;
                    bVal = b.kpi?.pbr ?? -Infinity;
                    break;
                case "dividendYield":
                    aVal = a.kpi?.dividendYield ?? -Infinity;
                    bVal = b.kpi?.dividendYield ?? -Infinity;
                    break;
                case "predicted12mReturn":
                    aVal = a.forecast?.predicted12mReturn ?? -Infinity;
                    bVal = b.forecast?.predicted12mReturn ?? -Infinity;
                    break;
            }

            if (aVal === undefined || aVal === null) aVal = -Infinity;
            if (bVal === undefined || bVal === null) bVal = -Infinity;

            if (typeof aVal === "string" && typeof bVal === "string") {
                return sortOrder === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }

            const numA = typeof aVal === "number" ? aVal : 0;
            const numB = typeof bVal === "number" ? bVal : 0;

            return sortOrder === "asc" ? numA - numB : numB - numA;
        });

        return result;
    }, [stocks, searchTerm, sortKey, sortOrder]);

    const SortIcon = ({ column }: { column: SortKey }) => {
        if (sortKey !== column) {
            return <span className="text-[var(--color-text-3)] opacity-50">↕</span>;
        }
        return <span className="text-[var(--color-brand-500)]">{sortOrder === "asc" ? "↑" : "↓"}</span>;
    };

    return (
        <div className="space-y-4">
            {/* 検索バー */}
            <div className="relative">
                <input
                    type="text"
                    placeholder="銘柄コード、名前、セクター、業種で検索..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-white/10 bg-[var(--color-surface-1)] text-[var(--color-text-1)] placeholder:text-[var(--color-text-3)] focus:outline-none focus:border-[var(--color-brand-500)] transition-colors"
                />
                {searchTerm && (
                    <button
                        onClick={() => setSearchTerm("")}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-3)] hover:text-[var(--color-text-1)] transition-colors"
                    >
                        ✕
                    </button>
                )}
            </div>

            {/* 結果件数 */}
            <div className="text-sm text-[var(--color-text-3)]">
                {filteredAndSortedStocks.length}件の銘柄
                {searchTerm && ` (全${stocks.length}件から絞り込み)`}
            </div>

            {/* テーブル */}
            <div className="overflow-x-auto rounded-xl border border-white/10 bg-[var(--color-surface-1)]">
                <table className="w-full">
                    <thead className="bg-[var(--color-surface-2)] border-b border-white/10">
                        <tr>
                            <th
                                className="px-4 py-3 text-left text-xs font-semibold text-[var(--color-text-2)] cursor-pointer hover:text-[var(--color-brand-500)] transition-colors select-none"
                                onClick={() => handleSort("ticker")}
                            >
                                <div className="flex items-center gap-1">
                                    銘柄コード
                                    <SortIcon column="ticker" />
                                </div>
                            </th>
                            <th
                                className="px-4 py-3 text-left text-xs font-semibold text-[var(--color-text-2)] cursor-pointer hover:text-[var(--color-brand-500)] transition-colors select-none"
                                onClick={() => handleSort("name")}
                            >
                                <div className="flex items-center gap-1">
                                    銘柄名
                                    <SortIcon column="name" />
                                </div>
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-[var(--color-text-2)]">
                                セクター / 業種
                            </th>
                            <th
                                className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-text-2)] cursor-pointer hover:text-[var(--color-brand-500)] transition-colors select-none"
                                onClick={() => handleSort("price")}
                            >
                                <div className="flex items-center justify-end gap-1">
                                    株価
                                    <SortIcon column="price" />
                                </div>
                            </th>
                            <th
                                className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-text-2)] cursor-pointer hover:text-[var(--color-brand-500)] transition-colors select-none"
                                onClick={() => handleSort("changePct")}
                            >
                                <div className="flex items-center justify-end gap-1">
                                    変動率
                                    <SortIcon column="changePct" />
                                </div>
                            </th>
                            <th
                                className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-text-2)] cursor-pointer hover:text-[var(--color-brand-500)] transition-colors select-none"
                                onClick={() => handleSort("per")}
                            >
                                <div className="flex items-center justify-end gap-1">
                                    PER
                                    <SortIcon column="per" />
                                </div>
                            </th>
                            <th
                                className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-text-2)] cursor-pointer hover:text-[var(--color-brand-500)] transition-colors select-none"
                                onClick={() => handleSort("pbr")}
                            >
                                <div className="flex items-center justify-end gap-1">
                                    PBR
                                    <SortIcon column="pbr" />
                                </div>
                            </th>
                            <th
                                className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-text-2)] cursor-pointer hover:text-[var(--color-brand-500)] transition-colors select-none"
                                onClick={() => handleSort("dividendYield")}
                            >
                                <div className="flex items-center justify-end gap-1">
                                    配当利回り
                                    <SortIcon column="dividendYield" />
                                </div>
                            </th>
                            <th
                                className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-text-2)] cursor-pointer hover:text-[var(--color-brand-500)] transition-colors select-none"
                                onClick={() => handleSort("predicted12mReturn")}
                            >
                                <div className="flex items-center justify-end gap-1">
                                    予測リターン
                                    <SortIcon column="predicted12mReturn" />
                                </div>
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredAndSortedStocks.length > 0 ? (
                            filteredAndSortedStocks.map((stock) => (
                                <tr
                                    key={stock.ticker}
                                    className="border-b border-white/5 last:border-0 hover:bg-[var(--color-surface-2)] transition-colors"
                                >
                                    <td className="px-4 py-3">
                                        <Link
                                            href={`/stocks/${stock.ticker}`}
                                            className="text-sm font-medium text-[var(--color-brand-500)] hover:underline"
                                        >
                                            {stock.ticker}
                                        </Link>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="text-sm font-medium text-[var(--color-text-1)]">{stock.name}</div>
                                        <div className="text-xs text-[var(--color-text-3)] mt-0.5">{stock.code}</div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="text-xs text-[var(--color-text-2)]">{stock.sector}</div>
                                        <div className="text-xs text-[var(--color-text-3)] mt-0.5">{stock.industry}</div>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <div className="text-sm font-medium text-[var(--color-text-1)]">
                                            {formatYen(stock.price)}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <Badge
                                            tone={stock.changePct >= 0 ? "success" : "danger"}
                                            size="sm"
                                        >
                                            {formatPercent(stock.changePct)}
                                        </Badge>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <span className="text-sm text-[var(--color-text-2)]">
                                            {stock.kpi?.per ? `${stock.kpi.per.toFixed(1)}x` : "N/A"}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <span className="text-sm text-[var(--color-text-2)]">
                                            {stock.kpi?.pbr ? `${stock.kpi.pbr.toFixed(1)}x` : "N/A"}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <span className="text-sm text-[var(--color-text-2)]">
                                            {stock.kpi?.dividendYield ? `${stock.kpi.dividendYield.toFixed(1)}%` : "N/A"}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        {stock.forecast?.predicted12mReturn !== undefined ? (
                                            <Badge
                                                tone={stock.forecast.predicted12mReturn >= 0 ? "success" : "danger"}
                                                size="sm"
                                            >
                                                {formatPercent(stock.forecast.predicted12mReturn)}
                                            </Badge>
                                        ) : (
                                            <span className="text-sm text-[var(--color-text-3)]">N/A</span>
                                        )}
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={9} className="px-4 py-12 text-center text-sm text-[var(--color-text-3)]">
                                    {searchTerm ? "検索条件に一致する銘柄が見つかりませんでした" : "銘柄データがありません"}
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
