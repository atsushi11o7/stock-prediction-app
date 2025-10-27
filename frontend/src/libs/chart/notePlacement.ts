// 注釈（吹き出し）自動配置のユーティリティ

import type { Series } from "./types";

export type XY = { x: number; y: number };
export type LineSeg = { x1: number; y1: number; x2: number; y2: number };


export type NotePlacementOptions = {
    plotX1: number;
    plotY1: number;
    plotX2: number;
    plotY2: number;
    predictStartIndex: number;
    xOfIndex: (i: number) => number;
    yOfValue: (v: number) => number;
    cols?: number;
    rows?: number;
    forecastBias?: number;
    noteWidth?: number;
    noteHeight?: number;
    inset?: number; // default 8
};

export type PlacementResult = {
    left: number;
    top: number;
    arrowSide: "top" | "right" | "bottom" | "left";
};

function collectSegmentsFromSeries(
    series: Series,
    xOf: (i: number) => number,
    yOf: (v: number) => number
): LineSeg[] {
    const segs: LineSeg[] = [];
    let prev: XY | null = null;
    for (let i = 0; i < series.length; i++) {
        const v = series[i];
        if (v == null || !Number.isFinite(v)) {
            prev = null;
            continue;
        }
        const p: XY = { x: xOf(i), y: yOf(v) };
        if (prev) {
            segs.push({ x1: prev.x, y1: prev.y, x2: p.x, y2: p.y });
        }
        prev = p;
    }
    return segs;
}

function distPointToSeg(px: number, py: number, s: LineSeg): number {
    const A = px - s.x1, B = py - s.y1, C = s.x2 - s.x1, D = s.y2 - s.y1;
    const dot = A * C + B * D;
    const lenSq = C * C + D * D || 1;
    const t = Math.max(0, Math.min(1, dot / lenSq));
    const ex = s.x1 + t * C, ey = s.y1 + t * D;
    const dx = px - ex, dy = py - ey;
    return Math.hypot(dx, dy);
}

function clamp(v: number, min: number, max: number) {
    return Math.max(min, Math.min(max, v));
}

/**
 * 折れ線群（実績/最新予測/過去予測）から「線から最も離れたグリッド点」を探し、ノート位置と矢印向きを返す。
 */
export function placeNoteAuto(
    actual: Series,
    predicted: Series,
    historical: Series[],
    labelsLength: number,
    opts: NotePlacementOptions
): PlacementResult {
    const {
        plotX1, plotY1, plotX2, plotY2,
        predictStartIndex,
        xOfIndex, yOfValue,
        cols = 8, rows = 4,
        forecastBias = 1.1,
        noteWidth = 320, noteHeight = 76,
        inset = 8,                            // ★ 追加
    } = opts;

    // 全セグメントを集約
    const segs: LineSeg[] = [];
    segs.push(...collectSegmentsFromSeries(actual, xOfIndex, yOfValue));
    segs.push(...collectSegmentsFromSeries(predicted, xOfIndex, yOfValue));
    for (const h of historical) {
        segs.push(...collectSegmentsFromSeries(h, xOfIndex, yOfValue));
    }

    const splitX = xOfIndex(predictStartIndex);

    // グリッド探索（線から最も離れた点を選ぶ。予測側に軽くバイアス）
    let best: { x: number; y: number; score: number } | null = null;
    for (let ci = 0; ci < cols; ci++) {
        for (let ri = 0; ri < rows; ri++) {
            const gx = plotX1 + ((ci + 0.5) / cols) * (plotX2 - plotX1);
            const gy = plotY1 + ((ri + 0.5) / rows) * (plotY2 - plotY1);

            let minDist = Number.POSITIVE_INFINITY;
            for (const s of segs) {
                const d = distPointToSeg(gx, gy, s);
                if (d < minDist) minDist = d;
            }

            const bias = gx >= splitX ? forecastBias : 1.0;
            const score = minDist * bias;

            if (!best || score > best.score) {
                best = { x: gx, y: gy, score };
            }
        }
    }

    const baseX = best?.x ?? (plotX1 + plotX2) / 2;
    const baseY = best?.y ?? (plotY1 + plotY2) / 2;

    // ノート左上（少し上寄せ）
    let left = baseX + 8;
    let top = baseY - noteHeight - 8;

    // ★ クランプに inset を考慮（縁に貼り付かない）
    left = clamp(left, plotX1 + inset, plotX2 - inset - noteWidth);
    top  = clamp(top,  plotY1 + inset, plotY2 - inset - noteHeight);

    let arrowSide: PlacementResult["arrowSide"] = "top";
    const margin = inset + 4; // ← 矢印判定も少し余裕を
    if (top <= plotY1 + margin) arrowSide = "bottom";
    if (left <= plotX1 + margin) arrowSide = "right";
    if (left >= plotX2 - noteWidth - margin) arrowSide = "left";

    return { left, top, arrowSide };
}