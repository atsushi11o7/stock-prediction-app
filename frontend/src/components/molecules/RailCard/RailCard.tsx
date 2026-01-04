"use client";

import clsx from "clsx";
import { baseCardClass, cardHoverLightClass, cardOverlayClass } from "@/libs/styles/cardStyles";

export default function RailCard({
    title,
    children,
    className,
}: {
    title: string;
    children?: React.ReactNode;
    className?: string;
}) {
    return (
        <section className={clsx(
            "group",
            baseCardClass,
            cardHoverLightClass,
            "p-5",
            className
        )}>
            <div className={cardOverlayClass}></div>
            <div className="relative">
                <h3 className="mb-4 text-sm font-bold text-[var(--color-text-2)] uppercase tracking-wide">
                    {title}
                </h3>
                {children}
            </div>
        </section>
    );
}