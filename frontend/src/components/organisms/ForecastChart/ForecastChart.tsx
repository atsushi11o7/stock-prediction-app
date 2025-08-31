"use client";

import React from "react";
import clsx from "clsx";

import MiniGrid from "@/components/molecules/MiniGrid";
import LineSeries from "@/components/molecules/LineSeries";
import SplitMarker from "@/components/molecules/SplitMarker";
import ForecastNote from "@/components/molecules/ForecastNote";

import { createLinear, niceDomain, extentFromSeries } from "@/libs/chart/scale";
import type { StockForecastData, Series } from "@/libs/chart/types";
import { placeNoteAuto } from "@/libs/chart/notePlacement";

export type ForecastChartProps = {
    data: StockForecastData;

    width?: number;
    height?: number;

    padding?: { top: number; right: number; bottom: number; left: number };

    showGrid?: boolean;
    gridRows?: number;
    gridCols?: number;
    gridDash?: string | null;

    showSplit?: boolean;
    splitLabel?: string;

    showNote?: boolean;
    showTickerLabel?: boolean;

    /** 過去予測を「今まで」にクリップするか（未来に伸ばさない）。既定: false（= 長さ自由） */
    historicalClipToNow?: boolean;

    /** 予測線の先頭を “現在（最後の実測点）” にアンカーして描画（視覚的ギャップをゼロに） */
    anchorAtCurrent?: boolean;

    /** 実測の終点と予測の始点を細線でつなぐ（アンカー無効時の視覚ギャップ対策）。既定: false */
    showJoinSegment?: boolean;

    colors?: {
        actual?: string;
        predicted?: string;
        predictedPast?: string;
        join?: string;   // 接続線の色（未指定なら predicted を利用）
    };

    className?: string;
};

/** 過去予測を“現在まで”にクリップ（未来側へは伸ばさない） */
function clipHistoricalToNow(values: Series, asOfIndex: number, predictStartIndex: number): Series {
    return values.map((v, i) => (i >= asOfIndex && i < predictStartIndex ? v : null));
}

export default function ForecastChart({
    data,
    width = 920,
    height = 460,
    padding = { top: 20, right: 16, bottom: 48, left: 56 },

    showGrid = true,
    gridRows = 3,
    gridCols = 6,
    gridDash = null,

    showSplit = true,
    splitLabel = "Forecast start",

    showNote = true,
    showTickerLabel = true,

    historicalClipToNow = false,
    anchorAtCurrent = true,     // ★ 既定で“現在アンカー”を付与
    showJoinSegment = false,    // ★ アンカーがあれば不要なので既定はオフ

    colors = {
        actual: "var(--color-brand-600)",         // 紫
        predicted: "#6DDB5E",                      // 緑
        predictedPast: "rgba(109,219,94,0.45)",    // 薄緑
        join: undefined,                           // 未指定なら predicted と同色
    },

    className,
}: ForecastChartProps) {
    const n = data.labels.length;

    // プロット領域
    const plotX1 = padding.left;
    const plotY1 = padding.top;
    const plotX2 = width - padding.right;
    const plotY2 = height - padding.bottom;

    // スケール
    const x = createLinear([0, n - 1], [plotX1, plotX2]);

    const allSeriesForExtent: Series[] = [
        data.actual,
        data.predicted,
        ...(data.historicalPredictions?.map(h => h.values) ?? []),
    ];
    const [yMin, yMax] = niceDomain(extentFromSeries(allSeriesForExtent), 4);
    const y = createLinear([yMin, yMax], [plotY2, plotY1]);

    const clip = { x1: plotX1, y1: plotY1, x2: plotX2, y2: plotY2 };

    // 過去予測の描画系列（クリップON/OFFを選べる。長さ自由に対応）
    const historicalToDraw: Series[] = (data.historicalPredictions ?? []).map(h =>
        historicalClipToNow ? clipHistoricalToNow(h.values, h.asOfIndex, data.predictStartIndex) : h.values
    );

    // ===== “現在（最後の実測点）” と “予測の最初の非null” を特定 =====
    const lastActualIndex = (() => {
        for (let i = Math.min(data.predictStartIndex, n) - 1; i >= 0; i--) {
            const v = data.actual[i];
            if (v != null && Number.isFinite(v)) return i;
        }
        return -1;
    })();

    const firstPredIndex = (() => {
        for (let i = data.predictStartIndex; i < n; i++) {
            const v = data.predicted[i];
            if (v != null && Number.isFinite(v)) return i;
        }
        return -1;
    })();

    const lastActualValue = lastActualIndex >= 0 ? (data.actual[lastActualIndex] as number) : null;

    // 予測線に “現在アンカー（仮想点）” を付加して描画用の series を作成（データ本体は変更しない）
    function buildPredictedWithAnchor(): Series {
        if (!anchorAtCurrent || lastActualIndex < 0 || lastActualValue == null) {
            return data.predicted;
        }
        const arr = [...data.predicted];
        if (arr[lastActualIndex] == null) {
            arr[lastActualIndex] = lastActualValue; // ← 見た目上の連続性を担保
        }
        return arr;
    }

    const predictedForDraw = buildPredictedWithAnchor();

    // 吹き出し自動配置
    const note = React.useMemo(() => {
        if (!showNote || !data.comment) return null;
        return placeNoteAuto(
            data.actual,
            predictedForDraw,
            historicalToDraw,
            n,
            {
                plotX1, plotY1, plotX2, plotY2,
                predictStartIndex: data.predictStartIndex,
                xOfIndex: (i) => x(i),
                yOfValue: (v) => y(v),
                cols: 8,
                rows: 4,
                forecastBias: 1.12,
                noteWidth: 320,
                noteHeight: 76,
                inset: 10, // 縁に貼り付かないよう内側にクランプ
            }
        );
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [JSON.stringify(data), width, height, showNote, historicalClipToNow, anchorAtCurrent]);

    // 接続セグメント（アンカー無効時のみ使う想定）
    const canJoin =
        showJoinSegment &&
        !anchorAtCurrent &&
        lastActualIndex >= 0 &&
        firstPredIndex >= 0;

    return (
        <figure
            className={clsx(
                "relative rounded-2xl border border-white/10 bg-[var(--color-panel)]",
                className
            )}
            style={{ width, height }}
        >
            <svg width={width} height={height} role="img" aria-label={`${data.ticker} forecast chart`}>
                {/* 背景グリッド */}
                {showGrid && (
                    <MiniGrid
                        x1={plotX1}
                        y1={plotY1}
                        x2={plotX2}
                        y2={plotY2}
                        rows={gridRows}
                        cols={gridCols}
                        dash={gridDash}
                        opacity={0.24}
                    />
                )}

                {/* 過去予測（複数・長さ自由） */}
                {historicalToDraw.map((s, idx) => (
                    <LineSeries
                        key={`hist-${idx}`}
                        series={s}
                        xOf={(i) => x(i)}
                        yOf={(v) => y(v)}
                        stroke={colors.predictedPast}
                        strokeWidth={2}
                        dash="6 6"
                        opacity={0.9}
                        clip={clip}
                    />
                ))}

                {/* 実測（紫） */}
                <LineSeries
                    series={data.actual}
                    xOf={(i) => x(i)}
                    yOf={(v) => y(v)}
                    stroke={colors.actual}
                    strokeWidth={3}
                    opacity={1}
                    clip={clip}
                />

                {/* 実測→予測の接続セグメント（アンカー無効時の視覚ギャップ対策） */}
                {canJoin && (
                    <line
                        x1={x(lastActualIndex)}
                        y1={y(data.actual[lastActualIndex] as number)}
                        x2={x(firstPredIndex)}
                        y2={y(data.predicted[firstPredIndex] as number)}
                        stroke={colors.join ?? colors.predicted ?? "#6DDB5E"}
                        strokeWidth={2}
                        strokeOpacity={0.7}
                        vectorEffect="non-scaling-stroke"
                    />
                )}

                {/* 予測（緑）— “現在アンカー” 付きの系列で描く */}
                <LineSeries
                    series={predictedForDraw}
                    xOf={(i) => x(i)}
                    yOf={(v) => y(v)}
                    stroke={colors.predicted}
                    strokeWidth={3}
                    opacity={1}
                    glow
                    glowOpacity={0.4}
                    glowWidth={10}
                    clip={clip}
                />

                {/* 予測開始マーカー：現在（最後の実測点）に合わせる */}
                {showSplit && lastActualIndex >= 0 && (
                    <SplitMarker
                        x={x(lastActualIndex)}
                        y1={plotY1}
                        y2={plotY2}
                        label={splitLabel}
                        labelSide="top"
                        clip={clip}
                    />
                )}
            </svg>

            {/* 自動配置ノート */}
            {showNote && data.comment && note && (
                <ForecastNote
                    title="Model note"
                    text={data.comment}
                    arrowSide={note.arrowSide}
                    style={{ left: note.left, top: note.top }}
                />
            )}

            {/* ティッカー（左上バッジ） */}
            {showTickerLabel && (
                <div
                    className="pointer-events-none absolute left-4 top-3 rounded-lg bg-[var(--color-surface-2)]/70 px-2 py-1 text-xs font-semibold text-[var(--color-text-2)]"
                    style={{ backdropFilter: "blur(2px)" }}
                    aria-hidden
                >
                    {data.ticker}
                </div>
            )}
        </figure>
    );
}