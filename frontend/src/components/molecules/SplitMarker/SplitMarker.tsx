"use client";

import React from "react";
import clsx from "clsx";

/**
 * 予測開始（過去→未来の切り替え点）を示す縦の点線。
 * - SVG 専用。<svg> 内で <g> として配置する想定です。
 * - ラベル（例: "Forecast start"）を任意で表示できます。
 */
export type SplitMarkerProps = {
    /** 縦線の x（px） */
    x: number;
    /** 縦線の上端 y（px） */
    y1: number;
    /** 縦線の下端 y（px） */
    y2: number;

    /** 線の色 */
    stroke?: string;
    /** 線の太さ（px） */
    strokeWidth?: number;
    /** 透明度（0..1） */
    opacity?: number;
    /** 点線パターン（例: "6 6"） */
    dash?: string;

    /** 線の上に小さな丸マーカーを付ける */
    showDot?: boolean;
    /** 丸マーカーの半径(px) */
    dotRadius?: number;

    /** ラベル表示 */
    showLabel?: boolean;
    /** ラベル文字列 */
    label?: string;
    /** ラベルの位置（線に対して上・右・下・左） */
    labelSide?: "top" | "right" | "bottom" | "left";
    /** ラベルのオフセット（px） */
    labelOffset?: number;
    /** ラベルのクラス名 */
    labelClassName?: string;

    /** クリッピング領域（プロット内に収めたい場合） */
    clip?: { x1: number; y1: number; x2: number; y2: number } | null;

    /** グループ要素のクラス名 */
    className?: string;

    /** アクセシビリティ（視覚表示のみなら true 推奨） */
    ariaHidden?: boolean;
};

type TextAnchor = "start" | "middle" | "end";

export default function SplitMarker({
    x,
    y1,
    y2,
    stroke = "var(--color-brand-600)",
    strokeWidth = 2,
    opacity = 0.9,
    dash = "6 6",
    showDot = true,
    dotRadius = 3,

    showLabel = true,
    label = "Forecast start",
    labelSide = "top",
    labelOffset = 8,
    labelClassName,

    clip = null,
    className,
    ariaHidden = true,
}: SplitMarkerProps) {
    const clipId = React.useId();
    const hasClip = !!clip;

    // ラベル座標を算出（簡易：線の中心基準）
    const midY = (y1 + y2) / 2;
    const labelPos: { x: number; y: number; anchor: TextAnchor; dy: string } = (() => {
        switch (labelSide) {
            case "top":
                return { x, y: y1 - labelOffset, anchor: "middle", dy: "-0.3em" };
            case "bottom":
                return { x, y: y2 + labelOffset, anchor: "middle", dy: "0.9em" };
            case "left":
                return { x: x - labelOffset, y: midY, anchor: "end", dy: "0.32em" };
            case "right":
            default:
                return { x: x + labelOffset, y: midY, anchor: "start", dy: "0.32em" };
        }
    })();

    return (
        <g aria-hidden={ariaHidden} className={clsx("split-marker-layer", className)}>
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

            {/* 縦の点線 */}
            <line
                x1={x}
                y1={y1}
                x2={x}
                y2={y2}
                stroke={stroke}
                strokeWidth={strokeWidth}
                strokeDasharray={dash}
                strokeOpacity={opacity}
                vectorEffect="non-scaling-stroke"
                clipPath={hasClip ? `url(#${clipId})` : undefined}
            />

            {/* 上端の小さな丸（任意） */}
            {showDot && (
                <circle
                    cx={x}
                    cy={y1}
                    r={dotRadius}
                    fill={stroke}
                    fillOpacity={opacity}
                    clipPath={hasClip ? `url(#${clipId})` : undefined}
                />
            )}

            {/* ラベル（任意） */}
            {showLabel && (
                <text
                    x={labelPos.x}
                    y={labelPos.y}
                    textAnchor={labelPos.anchor}
                    className={clsx("select-none text-[12px] font-medium", labelClassName)}
                    fill="var(--color-text-2)"
                    dy={labelPos.dy}
                >
                    {label}
                </text>
            )}
        </g>
    );
}