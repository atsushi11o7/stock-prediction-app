"use client";

import React from "react";
import clsx from "clsx";
import TickerCard, { type TickerCardProps } from "@/components/molecules/TickerCard";
import SeeAllCard from "@/components/molecules/SeeAllCard";

export type TickerItem = TickerCardProps;

export type TickerScrollerProps = {
    indices: TickerItem[];
    movers: TickerItem[];
    seeAll?: { href: string; label?: string };
    cardHeight?: number | string;
    className?: string;
};

export default function TickerScroller({
    indices,
    movers,
    seeAll,
    cardHeight = 88, // デフォルト
    className,
}: TickerScrollerProps) {
    const h = typeof cardHeight === "number" ? `${cardHeight}px` : cardHeight;
    type CSSVars = React.CSSProperties & { ["--scroll-card-h"]?: string };
    const styleVars: CSSVars = { ["--scroll-card-h"]: h };

    return (
        <section className={clsx("w-full", className)}>
            <div className={clsx("scroll-x", "overscroll-x-contain")}>
                <div className="flex items-stretch gap-3 pr-2" style={styleVars}>
                    {indices.map((it) => (
                        <TickerCard key={it.symbol} {...it} size="md" />
                    ))}

                    {movers.map((it) => (
                        <TickerCard key={it.symbol} {...it} size="sm" />
                    ))}

                    {seeAll ? (
                        <SeeAllCard href={seeAll.href} label={seeAll.label} />
                    ) : null}
                </div>
            </div>
        </section>
    );
}