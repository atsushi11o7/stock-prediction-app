"use client";

import React from "react";
import clsx from "clsx";

export type TickerCardProps = {
    symbol: string;
    name: string;
    price: number;
    changePct: number;
    size?: "sm" | "md";
    className?: string;
};

function yen(v: number) {
    return `¥${v.toLocaleString("ja-JP")}`;
}

function pct(v: number) {
    const s = `${v > 0 ? "+" : ""}${v.toFixed(2)}%`;
    return s;
}

export default function TickerCard({
    symbol,
    name,
    price,
    changePct,
    size = "md",
    className,
}: TickerCardProps) {
    const pad = size === "sm" ? "p-3" : "p-4";
    const title = size === "sm" ? "text-[11px]" : "text-xs";
    const priceCls = size === "sm" ? "text-base" : "text-lg";

    const tone =
        changePct > 0
            ? "text-[var(--color-success)]"
            : changePct < 0
            ? "text-[var(--color-danger)]"
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
                    {yen(price)}
                </div>
                <div className={clsx("mt-1 text-[12px] font-semibold", tone)}>
                    {pct(changePct)}
                </div>
            </div>
        </div>
    );
}