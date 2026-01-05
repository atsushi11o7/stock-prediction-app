"use client";

import React from "react";
import clsx from "clsx";

// ★ 変更点1: 固定版ではなくレスポンシブ版を使う
import ResponsiveForecastChart from "@/components/organisms/ForecastChart/ResponsiveForecastChart";
import type { ForecastChartProps } from "@/components/organisms/ForecastChart/ForecastChart";

import Legend from "@/components/molecules/Legend/Legend";
import MetricTile, { type MetricTileProps } from "@/components/molecules/MetricTile/MetricTile";

import type { StockForecastData } from "@/libs/chart/types";

export type Metric = {
    /** 表示ラベル（MetricTile の title にマップ） */
    label: string;
    /** 値 */
    value: string;
    /** あなたの実装の MetricTile に合わせる */
    tone?: MetricTileProps["tone"];
};

export type StockForecastCardProps = {
    data: StockForecastData;

    /** 見出し（未指定なら data.ticker を表示） */
    title?: string;
    /** サブ（会社名やセクタなど） */
    subtitle?: string;

    /** 右上などに小さく出すタグ（オプション） */
    tag?: string;

    /** 下部メトリクス（PER、Sector、Beta など） */
    metrics?: Metric[];

    /** 凡例の表示有無 */
    showLegend?: boolean;

    /** チャートの Note/スプリットの表示や配色など微調整 */
    chartProps?: Partial<ForecastChartProps>;

    className?: string;
};

/** カードのデフォルト配色（ForecastChart と揃える） */
const DEFAULT_COLORS: NonNullable<ForecastChartProps["colors"]> = {
    actual: "var(--color-brand-600)",      // 紫：実測
    predicted: "#6DDB5E",                   // 緑：将来予測
    predictedPast: "rgba(109,219,94,0.45)",// 薄緑：過去予測
    join: undefined,
};

export default function StockForecastCard({
    data,
    title,
    subtitle,
    tag,
    metrics = [],
    showLegend = true,
    chartProps,
    className,
}: StockForecastCardProps) {
    const colors = { ...DEFAULT_COLORS, ...(chartProps?.colors ?? {}) };

    return (
        <section
            className={clsx(
                "group relative overflow-hidden rounded-3xl border border-white/10",
                "bg-[var(--color-surface-1)]",
                "p-6 md:p-8 shadow-xl",
                "transition-all duration-300 hover:shadow-2xl hover:shadow-[var(--color-brand-500)]/10",
                className
            )}
            aria-label={`${data.ticker} stock forecast`}
        >
            {/* Overlay */}
            <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-all duration-300"></div>

            <div className="relative z-10">
            {/* ヘッダー */}
            <header className="mb-4 flex items-start justify-between gap-3">
                <div className="min-w-0">
                    <h2 className="truncate text-lg font-semibold text-[var(--color-text-1)]">
                        {title ?? data.ticker}
                    </h2>
                    {subtitle && (
                        <p className="mt-0.5 truncate text-sm text-[var(--color-text-3)]">{subtitle}</p>
                    )}
                </div>

                {tag && (
                    <span className="shrink-0 rounded-full bg-[var(--color-surface-2)]/70 px-2 py-1 text-[11px] font-semibold text-[var(--color-text-2)]">
                        {tag}
                    </span>
                )}
            </header>

            {/* 凡例（任意） */}
            {showLegend && (
                <div className="mb-3">
                    <Legend
                        items={[
                            { color: colors.actual!,        label: "Actual" },
                            { color: colors.predicted!,     label: "Forecast" },
                            { color: colors.predictedPast!, label: "Past Forecasts" },
                        ]}
                    />
                </div>
            )}

            {/* ★ 変更点2: チャートは親幅に追従（アスペクト比で高さ計算） */}
            <div className="mt-4">
                <ResponsiveForecastChart
                    data={data}
                    // 基本の見た目（必要に応じて chartProps で上書き）
                    padding={chartProps?.padding ?? { top: 20, right: 16, bottom: 52, left: 68 }}
                    showGrid={chartProps?.showGrid ?? true}
                    gridRows={chartProps?.gridRows ?? 3}
                    gridCols={chartProps?.gridCols ?? 6}
                    gridDash={chartProps?.gridDash ?? null}
                    showSplit={chartProps?.showSplit ?? true}
                    splitLabel={chartProps?.splitLabel ?? "Forecast start"}
                    showNote={chartProps?.showNote ?? true}
                    showTickerLabel={chartProps?.showTickerLabel ?? true}
                    historicalClipToNow={chartProps?.historicalClipToNow ?? false}
                    anchorAtCurrent={chartProps?.anchorAtCurrent ?? true}
                    animate={chartProps?.animate ?? true}
                    durations={chartProps?.durations ?? { revealTotalMs: 2200, fadeMs: 450, afterRevealDelayMs: 220 }}
                    colors={colors}
                    showAxes={chartProps?.showAxes ?? true}
                    yTickCount={chartProps?.yTickCount ?? 5}
                    xTickMonths={chartProps?.xTickMonths ?? [6, 12]}
                    xMaxTicks={chartProps?.xMaxTicks ?? 8}
                    yFormatter={chartProps?.yFormatter}
                    xFormatter={chartProps?.xFormatter}
                    // レスポンシブ指定
                    className="w-full"
                    aspectRatio={chartProps && "width" in chartProps ? undefined : 16 / 9}
                    minHeight={300}
                    maxHeight={520}
                />
            </div>

            {/* メトリクス */}
            {metrics.length > 0 && (
                <footer className="mt-5 grid gap-3 grid-cols-[repeat(auto-fit,minmax(200px,1fr))]">
                    {metrics.map((m, i) => (
                        <MetricTile
                            key={`${m.label}-${i}`}
                            title={m.label}
                            value={m.value}
                            tone={m.tone}
                        />
                    ))}
                </footer>
            )}

            </div>
        </section>
    );
}