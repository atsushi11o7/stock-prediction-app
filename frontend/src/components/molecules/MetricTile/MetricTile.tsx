"use client";

import React from "react";
import clsx from "clsx";

export type MetricTileProps = {
    title: string;                       // 見出し（例: "PER"）
    value: React.ReactNode;              // 値（例: "25.4"）
    hint?: string;                       // サブ情報（例: "TTM"）
    tone?: "neutral" | "up" | "down" | "brand";
    compact?: boolean;                   // コンパクト表示
    align?: "left" | "center" | "right";
    leading?: React.ReactNode;           // アイコン等を左に表示
    className?: string;
};

const toneClasses: Record<NonNullable<MetricTileProps["tone"]>, string> = {
    neutral: "text-[var(--color-text-1)]",
    up: "text-[var(--color-success)]",
    down: "text-[var(--color-danger)]",
    brand: "text-[var(--color-brand-600)]",
};

export default function MetricTile({
    title,
    value,
    hint,
    tone = "neutral",
    compact = false,
    align = "left",
    leading,
    className,
}: MetricTileProps) {
    const pad = compact ? "p-3" : "p-4";
    const titleSize = compact ? "text-[11px]" : "text-xs";
    const valueSize = compact ? "text-base" : "text-lg";

    return (
        <div
            className={clsx(
                "rounded-2xl border border-white/10 bg-[var(--color-surface-1)]",
                pad,
                className
            )}
        >
            <div
                className={clsx(
                    "flex items-start gap-3",
                    align === "center" && "justify-center",
                    align === "right" && "justify-end"
                )}
            >
                {leading && (
                    <div className="mt-[2px] shrink-0 text-[var(--color-text-3)]">
                        {leading}
                    </div>
                )}
                <div
                    className={clsx(
                        "min-w-0",
                        align === "center" && "text-center",
                        align === "right" && "text-right"
                    )}
                >
                    <div className={clsx(titleSize, "text-[var(--color-text-3)]")}>
                        {title}
                        {hint ? <span className="ml-1 opacity-70">• {hint}</span> : null}
                    </div>
                    <div
                        className={clsx(
                            valueSize,
                            "mt-1 font-semibold leading-tight",
                            toneClasses[tone]
                        )}
                    >
                        {value}
                    </div>
                </div>
            </div>
        </div>
    );
}