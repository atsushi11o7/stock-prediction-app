"use client";

import React from "react";
import clsx from "clsx";
import type { Series } from "@/libs/chart/types";

/**
 * 折れ線 1 本を描く（SVG 専用）
 * - series に null が含まれていると、その箇所で線を「分断」します
 * - xOf(index), yOf(value) でスケールを受け取り、座標を計算します
 * - dash（"6 6" 等）で点線化、glow で簡易発光（太めの半透明線を背面に）
 */
export type LineSeriesProps = {
    /** データ系列（null はギャップ） */
    series: Series;

    /** index -> x(px) 座標変換 */
    xOf: (i: number) => number;
    /** value -> y(px) 座標変換 */
    yOf: (v: number) => number;

    /** 線の色 */
    stroke?: string;
    /** 線の太さ（px） */
    strokeWidth?: number;
    /** 透明度（0..1） */
    opacity?: number;
    /** 丸角設定 */
    strokeLinecap?: "butt" | "round" | "square";
    strokeLinejoin?: "miter" | "round" | "bevel";
    /** 点線（例: "6 6"） */
    dash?: string | null;

    /** グロー（背面に太い半透明の線を描画） */
    glow?: boolean;
    glowOpacity?: number;   // 0..1
    glowWidth?: number;     // px

    /** クリッピング（プロット領域） */
    clip?: { x1: number; y1: number; x2: number; y2: number } | null;

    /** SVG グループに付けるクラス */
    className?: string;

    /** アクセシビリティ用。視覚化専用なら ariaHidden=true を推奨 */
    ariaHidden?: boolean;
};

export default function LineSeries({
    series,
    xOf,
    yOf,
    stroke = "#7a23d4",        // brand-600 相当（紫）
    strokeWidth = 3,
    opacity = 1,
    strokeLinecap = "round",
    strokeLinejoin = "round",
    dash = null,
    glow = false,
    glowOpacity = 0.5,
    glowWidth = Math.max(6, strokeWidth * 2),
    clip = null,
    className,
    ariaHidden = true,
}: LineSeriesProps) {
    // null で分割された「サブパス」配列を作る
    const segs: Array<Array<{ x: number; y: number }>> = [];
    let curr: Array<{ x: number; y: number }> = [];

    for (let i = 0; i < series.length; i++) {
        const v = series[i];
        if (v == null || !Number.isFinite(v)) {
            if (curr.length > 1) segs.push(curr);
            curr = [];
            continue;
        }
        const x = xOf(i);
        const y = yOf(v);
        curr.push({ x, y });
    }
    if (curr.length > 1) segs.push(curr);

    // SVG path d を生成
    const toPath = (pts: Array<{ x: number; y: number }>) => {
        let d = `M ${pts[0].x} ${pts[0].y}`;
        for (let k = 1; k < pts.length; k++) {
            d += ` L ${pts[k].x} ${pts[k].y}`;
        }
        return d;
    };

    // クリップパス（任意）
    const clipId = React.useId();
    const hasClip = !!clip;

    return (
        <g
            aria-hidden={ariaHidden}
            className={clsx("line-series-layer", className)}
        >
            {hasClip && clip && (
                <clipPath id={clipId}>
                    <rect
                        x={clip.x1}
                        y={clip.y1}
                        width={Math.max(0, clip.x2 - clip.x1)}
                        height={Math.max(0, clip.y2 - clip.y1)}
                    />
                </clipPath>
            )}

            {/* glow（背面） */}
            {glow && segs.map((pts, i) => (
                <path
                    key={`glow-${i}`}
                    d={toPath(pts)}
                    fill="none"
                    stroke={stroke}
                    strokeWidth={glowWidth}
                    strokeLinecap={strokeLinecap}
                    strokeLinejoin={strokeLinejoin}
                    strokeOpacity={glowOpacity}
                    clipPath={hasClip ? `url(#${clipId})` : undefined}
                    style={{ filter: "blur(0.2px)" }} // 軽いソフト化
                />
            ))}

            {/* 本線 */}
            {segs.map((pts, i) => (
                <path
                    key={`line-${i}`}
                    d={toPath(pts)}
                    fill="none"
                    stroke={stroke}
                    strokeWidth={strokeWidth}
                    strokeLinecap={strokeLinecap}
                    strokeLinejoin={strokeLinejoin}
                    strokeOpacity={opacity}
                    strokeDasharray={dash ?? undefined}
                    clipPath={hasClip ? `url(#${clipId})` : undefined}
                />
            ))}
        </g>
    );
}