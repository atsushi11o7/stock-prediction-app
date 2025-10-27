"use client";

import React from "react";
import clsx from "clsx";

export type Series = (number | null)[];

export type LineSeriesProps = {
    /** 値の配列。null の箇所はギャップ（線を切る） */
    series: Series;

    /** x 軸：index -> px */
    xOf: (i: number) => number;
    /** y 軸：value -> px */
    yOf: (v: number) => number;

    /** 線色（CSS color） */
    stroke?: string;
    /** 線の太さ */
    strokeWidth?: number;
    /** 透明度 */
    opacity?: number;

    /** stroke-dasharray に渡すパターン（"6 6" など） */
    dash?: string | null;

    /** 丸/角など */
    strokeLinecap?: "butt" | "round" | "square";
    strokeLinejoin?: "miter" | "round" | "bevel";

    /** クリップ矩形（描画範囲） */
    clip?: { x1: number; y1: number; x2: number; y2: number };

    /** ふわっと光る外側グロー（疑似） */
    glow?: boolean;
    glowWidth?: number;     // 例: 10
    glowOpacity?: number;   // 例: 0.35

    /** 線を“徐々に描く”アニメを有効化 */
    animateDraw?: boolean;
    /** 描画にかける時間（ms） */
    durationMs?: number;
    /** 開始までのディレイ（ms） */
    delayMs?: number;
    /** 描き終わったときのコールバック（オーケストレーション用） */
    onDrawEnd?: () => void;

    className?: string;
};

function buildPathD(series: Series, xOf: (i: number) => number, yOf: (v: number) => number): string {
    let d = "";
    let penDown = false;
    for (let i = 0; i < series.length; i++) {
        const v = series[i];
        if (v == null || !Number.isFinite(v)) {
            penDown = false;
            continue;
        }
        const x = xOf(i);
        const y = yOf(v);
        if (!penDown) {
            d += `M ${x} ${y}`;
            penDown = true;
        } else {
            d += ` L ${x} ${y}`;
        }
    }
    return d || "M 0 0";
}

let gid = 0;

export default function LineSeries({
    series,
    xOf,
    yOf,
    stroke = "currentColor",
    strokeWidth = 2,
    opacity = 1,
    dash = null,
    strokeLinecap = "round",
    strokeLinejoin = "round",
    clip,
    glow = false,
    glowWidth = 10,
    glowOpacity = 0.35,
    animateDraw = false,
    durationMs = 1200,
    delayMs = 0,
    onDrawEnd,
    className,
}: LineSeriesProps) {
    const d = React.useMemo(() => buildPathD(series, xOf, yOf), [series, xOf, yOf]);

    const pathRef = React.useRef<SVGPathElement | null>(null);
    const [clipId] = React.useState(() => (clip ? `clip-${++gid}` : undefined));
    const [glowId] = React.useState(() => (glow ? `glow-${++gid}` : undefined));

    React.useEffect(() => {
        if (!animateDraw || !pathRef.current) return;
        const el = pathRef.current;
        const total = el.getTotalLength();

        // 初期化
        el.style.strokeDasharray = String(total);
        el.style.strokeDashoffset = String(total);
        el.style.transition = "none";

        const t = setTimeout(() => {
            el.style.transition = `stroke-dashoffset ${durationMs}ms ease`;
            el.style.strokeDashoffset = "0";

            const done = setTimeout(() => onDrawEnd?.(), durationMs);
            return () => clearTimeout(done);
        }, delayMs);

        return () => clearTimeout(t);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [d, animateDraw, durationMs, delayMs]);

    return (
        <>
            {clip && (
                <defs>
                    <clipPath id={clipId}>
                        <rect
                            x={clip.x1}
                            y={clip.y1}
                            width={clip.x2 - clip.x1}
                            height={clip.y2 - clip.y1}
                            rx={0}
                            ry={0}
                        />
                    </clipPath>
                </defs>
            )}

            {glow && (
                <defs>
                    <filter id={glowId} x="-50%" y="-50%" width="200%" height="200%">
                        <feGaussianBlur in="SourceGraphic" stdDeviation={glowWidth / 2} result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>
            )}

            {/* グロー用の太い下地（半透明） */}
            {glow && (
                <path
                    d={d}
                    clipPath={clipId ? `url(#${clipId})` : undefined}
                    className={clsx(className)}
                    fill="none"
                    stroke={stroke}
                    strokeWidth={glowWidth}
                    strokeOpacity={glowOpacity}
                    strokeLinecap={strokeLinecap}
                    strokeLinejoin={strokeLinejoin}
                    vectorEffect="non-scaling-stroke"
                    filter={glowId ? `url(#${glowId})` : undefined}
                />
            )}

            {/* 本体線 */}
            <path
                ref={pathRef}
                d={d}
                clipPath={clipId ? `url(#${clipId})` : undefined}
                className={clsx(className)}
                fill="none"
                stroke={stroke}
                strokeWidth={strokeWidth}
                strokeOpacity={opacity}
                strokeLinecap={strokeLinecap}
                strokeLinejoin={strokeLinejoin}
                vectorEffect="non-scaling-stroke"
                strokeDasharray={dash ?? undefined}
            />
        </>
    );
}