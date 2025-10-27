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

    /** 過去予測を“今まで”にクリップ（未来へ伸ばさない） */
    historicalClipToNow?: boolean;

    /** 予測線の先頭を“現在（最後の実測点）”にアンカー */
    anchorAtCurrent?: boolean;

    /** 実測→予測の順でマスク開示アニメ（光りは無し） */
    animate?: boolean;

    durations?: {
        revealTotalMs: number;
        fadeMs: number;
        afterRevealDelayMs: number;
    };

    colors?: {
        actual?: string;
        predicted?: string;
        predictedPast?: string;
        join?: string;
    };

    /** 軸の表示 */
    showAxes?: boolean;
    /** Y軸 tick 数（目安） */
    yTickCount?: number;

    /**
     * X 軸ラベルを付ける“月番号（1-12）”の集合。
     * 既定は [6, 12]（= 6月と12月）。
     * null を渡すと、この制御は無効化され、xMaxTicks/等間隔サンプリングの挙動に戻ります。
     */
    xTickMonths?: number[] | null;
    /** X軸ラベルの最大数（xTickMonths が null のときのみ使用） */
    xMaxTicks?: number;

    /** フォーマット関数（上書き可能） */
    yFormatter?: (v: number) => string;
    xFormatter?: (label: string) => string;

    className?: string;
};

function clipHistoricalToNow(values: Series, asOfIndex: number, predictStartIndex: number): Series {
    return values.map((v, i) => (i >= asOfIndex && i < predictStartIndex ? v : null));
}

let gid = 0;

export default function ForecastChart({
    data,
    width = 920,
    height = 460,
    padding = { top: 20, right: 16, bottom: 52, left: 68 }, // 軸ラベルぶん少し広め

    showGrid = true,
    gridRows = 3,
    gridCols = 6,
    gridDash = null,

    showSplit = true,
    splitLabel = "Forecast start",

    showNote = true,
    showTickerLabel = true,

    historicalClipToNow = false,
    anchorAtCurrent = true,

    animate = true,
    durations = { revealTotalMs: 2200, fadeMs: 450, afterRevealDelayMs: 220 },

    colors = {
        actual: "var(--color-brand-600)",
        predicted: "#6DDB5E",
        predictedPast: "rgba(109,219,94,0.45)",
        join: undefined,
    },

    // 軸関連
    showAxes = true,
    yTickCount = 5,

    // ★ 追加：6月＆12月に限定
    xTickMonths = [6, 12],
    xMaxTicks = 8,

    yFormatter,
    xFormatter,

    className,
}: ForecastChartProps) {
    const n = data.labels.length;

    // プロット領域（軸ラベル等の余白を除いた内側）
    const plotX1 = padding.left;
    const plotY1 = padding.top;
    const plotX2 = width - padding.right;
    const plotY2 = height - padding.bottom;

    // スケール
    const x = createLinear([0, n - 1], [plotX1, plotX2]);

    const allSeriesForExtent: Series[] = [
        data.actual,
        data.predicted,
        ...(data.historicalPredictions?.map((h) => h.values) ?? []),
    ];
    const [yMin, yMax] = niceDomain(extentFromSeries(allSeriesForExtent), 4);
    const y = createLinear([yMin, yMax], [plotY2, plotY1]);

    // Y軸 tick（等間隔）
    const yTicks: number[] = React.useMemo(() => {
        const count = Math.max(2, yTickCount | 0);
        const step = (yMax - yMin) / (count - 1);
        const arr: number[] = [];
        for (let i = 0; i < count; i++) arr.push(yMin + step * i);
        return arr;
    }, [yMin, yMax, yTickCount]);

    // X軸 tick：既定は 6月＆12月にのみラベル
    const xTicks: number[] = React.useMemo(() => {
        // 月限定（xTickMonths）を優先
        if (xTickMonths && xTickMonths.length > 0) {
            const wanted = new Set(xTickMonths.map((m) => Math.max(1, Math.min(12, m))));
            const arr: number[] = [];
            for (let i = 0; i < n; i++) {
                const lab = data.labels[i]; // "YYYY-MM" 想定
                const mm = Number(lab.slice(5, 7));
                if (wanted.has(mm)) arr.push(i);
            }
            // もし 1 個も取れなかった場合の保険：末尾だけは出す
            if (arr.length === 0 && n > 0) arr.push(n - 1);
            return arr;
        }
        // 従来ロジック（最大数で等間隔）
        const max = Math.max(2, xMaxTicks | 0);
        if (n <= max) return Array.from({ length: n }, (_, i) => i);
        const step = (n - 1) / (max - 1);
        const set = new Set<number>();
        for (let i = 0; i < max; i++) set.add(Math.floor(step * i));
        set.add(n - 1);
        return Array.from(set);
    }, [n, xMaxTicks, xTickMonths, data.labels]);

    // フォーマッタ
    const yen = React.useMemo(
        () => (v: number) => `${new Intl.NumberFormat("ja-JP").format(Math.round(v))}円`,
        []
    );
    const fmtY = yFormatter ?? yen;
    const fmtX = xFormatter ?? ((lab: string) => lab); // labels は "YYYY-MM" の想定

    // “現在（最後の実測点）”
    const lastActualIndex = (() => {
        for (let i = Math.min(data.predictStartIndex, n) - 1; i >= 0; i--) {
            const v = data.actual[i];
            if (v != null && Number.isFinite(v)) return i;
        }
        return -1;
    })();
    const lastActualValue = lastActualIndex >= 0 ? (data.actual[lastActualIndex] as number) : null;

    // 予測のアンカー＝実測終点へ連続
    const predictedForDraw: Series = React.useMemo(() => {
        if (!anchorAtCurrent || lastActualIndex < 0 || lastActualValue == null) {
            return data.predicted;
        }
        const arr = [...data.predicted];
        if (arr[lastActualIndex] == null) {
            arr[lastActualIndex] = lastActualValue;
        }
        return arr;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [JSON.stringify(data.predicted), anchorAtCurrent, lastActualIndex, lastActualValue]);

    // 過去予測
    const historicalToDraw: Series[] = (data.historicalPredictions ?? []).map((h) =>
        historicalClipToNow ? clipHistoricalToNow(h.values, h.asOfIndex, data.predictStartIndex) : h.values
    );

    // SVG クリップ
    const [clipActualId] = React.useState(() => `clip-actual-${++gid}`);
    const [clipPredId] = React.useState(() => `clip-pred-${++gid}`);

    // ====== マスク開示アニメ：左→右に進行する progressX（px） ======
    const [progressX, setProgressX] = React.useState(plotX1);
    const [fullyRevealed, setFullyRevealed] = React.useState(!animate);
    const revealStartTs = React.useRef<number | null>(null);

    React.useEffect(() => {
        if (!animate) {
            setProgressX(plotX2);
            setFullyRevealed(true);
            return;
        }
        let raf = 0;
        const totalMs = durations.revealTotalMs;
        const ease = (t: number) => 1 - Math.pow(1 - t, 3); // easeOutCubic
        const loop = (now: number) => {
            if (revealStartTs.current == null) revealStartTs.current = now;
            const t = Math.min(1, (now - revealStartTs.current) / totalMs);
            const eased = ease(t);
            const px = plotX1 + (plotX2 - plotX1) * eased;
            setProgressX(px);
            if (t < 1) {
                raf = requestAnimationFrame(loop);
            } else {
                setFullyRevealed(true);
            }
        };
        raf = requestAnimationFrame(loop);
        return () => cancelAnimationFrame(raf);
    }, [animate, durations.revealTotalMs, plotX1, plotX2]);

    // 実測は progressX に追従、予測は“現在”から右側のみ開示
    const splitX = lastActualIndex >= 0 ? x(lastActualIndex) : x(data.predictStartIndex);
    const actualClipWidth = Math.max(0, Math.min(progressX, plotX2) - plotX1);
    const predClipWidth = Math.max(0, Math.min(progressX - splitX, plotX2 - splitX));

    // Note 自動配置（全開示後の見栄えに合わせる）
    const notePlacement = React.useMemo(() => {
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
                inset: 10,
            }
        );
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [JSON.stringify(data), width, height, showNote, historicalClipToNow, anchorAtCurrent]);

    // フェードインのトリガ
    const [showNoteHist, setShowNoteHist] = React.useState(!animate);
    React.useEffect(() => {
        if (!animate) return;
        if (fullyRevealed) {
            const t = setTimeout(() => setShowNoteHist(true), durations.afterRevealDelayMs);
            return () => clearTimeout(t);
        }
    }, [animate, fullyRevealed, durations.afterRevealDelayMs]);

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

                {/* クリップ定義（実測/予測） */}
                <defs>
                    <clipPath id={clipActualId}>
                        <rect x={plotX1} y={plotY1} width={actualClipWidth} height={plotY2 - plotY1} />
                    </clipPath>
                    <clipPath id={clipPredId}>
                        <rect x={splitX} y={plotY1} width={predClipWidth} height={plotY2 - plotY1} />
                    </clipPath>
                </defs>

                {/* --- 軸（Y 左 / X 下）--- */}
                {showAxes && (
                    <>
                        {/* Y軸線 */}
                        <line
                            x1={plotX1}
                            x2={plotX1}
                            y1={plotY1}
                            y2={plotY2}
                            stroke="rgba(255,255,255,0.2)"
                            strokeWidth={1}
                        />
                        {/* Y軸目盛＋ラベル */}
                        {yTicks.map((tv, i) => {
                            const yy = y(tv);
                            return (
                                <g key={`yt-${i}`} transform={`translate(0, ${yy})`}>
                                    <line
                                        x1={plotX1 - 6}
                                        x2={plotX1}
                                        y1={0}
                                        y2={0}
                                        stroke="rgba(255,255,255,0.35)"
                                        strokeWidth={1}
                                    />
                                    <text
                                        x={plotX1 - 8}
                                        y={0}
                                        textAnchor="end"
                                        dominantBaseline="middle"
                                        fill="var(--color-text-3)"
                                        fontSize={11}
                                    >
                                        {fmtY(tv)}
                                    </text>
                                </g>
                            );
                        })}

                        {/* X軸線 */}
                        <line
                            x1={plotX1}
                            x2={plotX2}
                            y1={plotY2}
                            y2={plotY2}
                            stroke="rgba(255,255,255,0.2)"
                            strokeWidth={1}
                        />
                        {/* X軸ラベル（6月/12月のみ） */}
                        {xTicks.map((idx, i) => {
                            const xx = x(idx);
                            return (
                                <g key={`xt-${i}`} transform={`translate(${xx}, 0)`}>
                                    <line
                                        x1={0}
                                        x2={0}
                                        y1={plotY2}
                                        y2={plotY2 + 4}
                                        stroke="rgba(255,255,255,0.35)"
                                        strokeWidth={1}
                                    />
                                    <text
                                        x={0}
                                        y={plotY2 + 16}
                                        textAnchor="middle"
                                        dominantBaseline="hanging"
                                        fill="var(--color-text-3)"
                                        fontSize={11}
                                    >
                                        {fmtX(data.labels[idx])}
                                    </text>
                                </g>
                            );
                        })}
                    </>
                )}

                {/* 過去予測（後からフェード） */}
                <g style={{ opacity: showNoteHist ? 1 : 0, transition: `opacity ${durations.fadeMs}ms ease` }}>
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
                            clip={{ x1: plotX1, y1: plotY1, x2: plotX2, y2: plotY2 }}
                        />
                    ))}
                </g>

                {/* 実測（紫）— 左→右に開示 */}
                <g clipPath={`url(#${clipActualId})`}>
                    <LineSeries
                        series={data.actual}
                        xOf={(i) => x(i)}
                        yOf={(v) => y(v)}
                        stroke={colors.actual}
                        strokeWidth={3}
                        opacity={1}
                        clip={{ x1: plotX1, y1: plotY1, x2: plotX2, y2: plotY2 }}
                    />
                </g>

                {/* 予測（緑）— “現在”を起点に右へ開示 */}
                <g clipPath={`url(#${clipPredId})`}>
                    <LineSeries
                        series={predictedForDraw}
                        xOf={(i) => x(i)}
                        yOf={(v) => y(v)}
                        stroke={colors.predicted}
                        strokeWidth={3}
                        opacity={1}
                        clip={{ x1: plotX1, y1: plotY1, x2: plotX2, y2: plotY2 }}
                    />
                </g>

                {/* 予測開始マーカー：上下に少し余白を取り、グラフ枠とラベルの重なりを回避 */}
                {showSplit && lastActualIndex >= 0 && (
                    <SplitMarker
                        x={splitX}
                        y1={plotY1 + 8}   // ← 上から 8px 下げる
                        y2={plotY2 - 2}   // ← 下から 2px 上げる
                        label={splitLabel}
                        labelSide="top"
                        clip={{ x1: plotX1, y1: plotY1, x2: plotX2, y2: plotY2 }}
                    />
                )}
            </svg>

            {/* 吹き出し（後からフェード） */}
            {showNote && data.comment && notePlacement && (
                <div style={{ opacity: showNoteHist ? 1 : 0, transition: `opacity ${durations.fadeMs}ms ease` }}>
                    <ForecastNote
                        title="Model note"
                        text={data.comment}
                        arrowSide={notePlacement.arrowSide}
                        style={{ left: notePlacement.left, top: notePlacement.top }}
                    />
                </div>
            )}

            {/* ティッカー（左上バッジ）— 軸ラベルと重ならないようプロット左上基準で配置 */}
            {showTickerLabel && (
                <div
                    className="pointer-events-none absolute rounded-lg bg-[var(--color-surface-2)]/70 px-2 py-1 text-xs font-semibold text-[var(--color-text-2)]"
                    style={{
                        left: plotX1 + 8,   // ← Y軸ラベル外、プロット内
                        top: plotY1 + 6,    // ← 上辺から少し下げる
                        backdropFilter: "blur(2px)",
                    }}
                    aria-hidden
                >
                    {data.ticker}
                </div>
            )}
        </figure>
    );
}