"use client";

import React from "react";
import clsx from "clsx";

export type ForecastNoteProps = {
    /** 小見出し（例: "Model note"） */
    title?: string;
    /** 本文（改行可） */
    text: string;
    /** テール（矢印）の向き */
    arrowSide?: "top" | "right" | "bottom" | "left";
    /** テール表示の有無 */
    showArrow?: boolean;
    /** 最大幅（px）。未指定なら 300px */
    maxWidth?: number;
    /** 絶対配置用の style。親が relative を持つ前提 */
    style?: React.CSSProperties;
    /** 外観のトーン（将来拡張・今は surface ベース） */
    tone?: "default";
    className?: string;
};

export default function ForecastNote({
    title = "Model note",
    text,
    arrowSide = "top",
    showArrow = true,
    maxWidth = 300,
    style,
    tone = "default",
    className,
}: ForecastNoteProps) {
    // テール（矢印）は 8px の正方形を 45度回転して表現
    const arrow = (
        <span
            aria-hidden
            className={clsx(
                "absolute block h-2 w-2 rotate-45 border border-white/10",
                "bg-[var(--color-surface-1)]/90 shadow-sm"
            )}
            style={{
                ...(arrowSide === "top" && { left: 16, top: -4 }),
                ...(arrowSide === "right" && { right: -4, top: 16 }),
                ...(arrowSide === "bottom" && { left: 16, bottom: -4 }),
                ...(arrowSide === "left" && { left: -4, top: 16 }),
            }}
        />
    );

    return (
        <div
            className={clsx(
                "pointer-events-none absolute select-none",
                "rounded-xl border border-white/10",
                "bg-[var(--color-surface-1)]/90 p-3 shadow-sm",
                "text-xs text-[var(--color-text-2)] backdrop-blur-[1px]",
                className
            )}
            style={{ maxWidth, ...style }}
            role="note"
            aria-label={title}
        >
            {showArrow && arrowSide === "top" && arrow}
            <div className="mb-1 text-[10px] uppercase tracking-wide text-[var(--color-text-3)]">
                {title}
            </div>
            <p className="whitespace-pre-line leading-relaxed">
                {text}
            </p>
            {showArrow && arrowSide !== "top" && arrow}
        </div>
    );
}