"use client";

import React from "react";
import clsx from "clsx";
import { formatYen, formatPercent } from "@/libs/utils/formatters";
import { cardPaddingSizeMap, textSizeMap } from "@/libs/styles/sizeUtils";
import { textColorMap } from "@/libs/styles/colorThemes";

export type TickerCardProps = {
    symbol: string;
    name: string;
    price: number;
    changePct: number;
    size?: "sm" | "md";
    className?: string;
};

export default function TickerCard({
    symbol,
    name,
    price,
    changePct,
    size = "md",
    className,
}: TickerCardProps) {
    const pad = cardPaddingSizeMap[size];
    const title = size === "sm" ? textSizeMap.xs : textSizeMap.md;
    const priceCls = size === "sm" ? textSizeMap.lg : textSizeMap.xl;

    const tone =
        changePct > 0
            ? textColorMap.success
            : changePct < 0
            ? textColorMap.danger
            : "text-[var(--color-text-2)]";

    return (
        <div
            className={clsx(
                "min-h-[var(--scroll-card-h,88px)] h-auto",
                "flex flex-col justify-between",
                "rounded-2xl border border-white/10 bg-[var(--color-surface-1)] w-[180px] shrink-0",
                pad,
                className
            )}
            role="group"
            aria-label={`${name} card`}
        >
            <div>
                <div className="text-[10px] font-semibold text-[var(--color-text-3)]">
                    {symbol}
                </div>
                <div
                    className={clsx(
                        "mt-0.5 font-semibold text-[var(--color-text-1)] line-clamp-1 break-words",
                        title
                    )}
                >
                    {name}
                </div>
            </div>

            <div>
                <div className={clsx("mt-2 font-semibold leading-tight", priceCls)}>
                    {formatYen(price)}
                </div>
                <div className={clsx("mt-1 text-[12px] font-semibold", tone)}>
                    {formatPercent(changePct)}
                </div>
            </div>
        </div>
    );
}