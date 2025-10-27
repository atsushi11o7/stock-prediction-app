"use client";

import React from "react";
import clsx from "clsx";

/**
 * チャートのプロット領域内に薄いガイド線を描くレイヤー（SVG 内で <g> として使用）
 *
 * 想定：
 * <svg ...>
 *   <MiniGrid x1={40} y1={16} x2={780} y2={320} rows={3} cols={6} />
 *   ... 他のレイヤー（軸、折れ線など）
 * </svg>
 */
export type MiniGridProps = {
    /** プロット領域の左上 (x1, y1) と右下 (x2, y2) */
    x1: number;
    y1: number;
    x2: number;
    y2: number;

    /** 水平線（行）の本数。0 の場合は描かない。デフォルト 3 */
    rows?: number;

    /** 垂直線（列）の本数。未指定なら描かない */
    cols?: number;

    /** 線色（未指定なら CSS 変数ベースの控えめな色） */
    stroke?: string;

    /** 線の太さ（px） */
    strokeWidth?: number;

    /** 透明度（0〜1） */
    opacity?: number;

    /** 点線（"4 4" のような strokeDasharray を受け付け） */
    dash?: string | null;

    /** 最外枠（plot ボックス）の描画をするか */
    showBorder?: boolean;

    className?: string;
};

export default function MiniGrid({
    x1,
    y1,
    x2,
    y2,
    rows = 3,
    cols,
    stroke,
    strokeWidth = 1,
    opacity = 0.28,
    dash = null,
    showBorder = false,
    className,
}: MiniGridProps) {
    const w = Math.max(0, x2 - x1);
    const h = Math.max(0, y2 - y1);

    const sx = stroke ?? "rgba(255,255,255,0.28)"; // 画像モックに近い控えめな白
    const common = {
        stroke: sx,
        strokeWidth,
        opacity,
        strokeDasharray: dash ?? undefined,
        vectorEffect: "non-scaling-stroke" as const,
    };

    const horizontals: React.ReactNode[] = [];
    if (rows > 0) {
        for (let i = 0; i <= rows; i++) {
            const t = rows === 0 ? 0 : i / rows;
            const y = y1 + h * t;
            horizontals.push(
                <line
                    key={`h-${i}`}
                    x1={x1}
                    y1={y}
                    x2={x2}
                    y2={y}
                    {...common}
                />
            );
        }
    }

    const verticals: React.ReactNode[] = [];
    if (typeof cols === "number" && cols > 0) {
        for (let j = 0; j <= cols; j++) {
            const t = cols === 0 ? 0 : j / cols;
            const x = x1 + w * t;
            verticals.push(
                <line
                    key={`v-${j}`}
                    x1={x}
                    y1={y1}
                    x2={x}
                    y2={y2}
                    {...common}
                />
            );
        }
    }

    return (
        <g
            aria-hidden
            className={clsx("mini-grid-layer", className)}
        >
            {showBorder && (
                <rect
                    x={x1}
                    y={y1}
                    width={w}
                    height={h}
                    fill="none"
                    {...common}
                    opacity={Math.min(1, opacity * 0.8)}
                />
            )}
            {horizontals}
            {verticals}
        </g>
    );
}