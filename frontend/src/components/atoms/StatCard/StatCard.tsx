// src/components/atoms/StatCard/StatCard.tsx
"use client";

import React from "react";
import clsx from "clsx";
import { textColorMap, type TextColorTone } from "@/libs/styles/colorThemes";
import { baseCardClass, cardHoverMediumClass, cardOverlayClass } from "@/libs/styles/cardStyles";

export type StatCardProps = {
    /** Main label/title */
    label: string;
    /** Primary value to display */
    value: string;
    /** Optional secondary value (e.g., percentage, subtitle) */
    subvalue?: string;
    /** Visual tone for the value */
    tone?: TextColorTone;
    /** Optional icon to display */
    icon?: React.ReactNode;
    /** Custom className */
    className?: string;
};

export default function StatCard({
    label,
    value,
    subvalue,
    tone = "neutral",
    icon,
    className,
}: StatCardProps) {
    return (
        <div
            className={clsx(
                "group",
                baseCardClass,
                cardHoverMediumClass,
                "px-5 py-4 backdrop-blur-sm",
                className
            )}
        >
            {/* Overlay */}
            <div className={cardOverlayClass}></div>

            <div className="relative z-10">
                <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                        <p className="text-xs text-[var(--color-text-3)] font-medium uppercase tracking-wide">
                            {label}
                        </p>
                        <p className={clsx("mt-1 text-2xl font-bold tabular-nums", textColorMap[tone])}>
                            {value}
                        </p>
                        {subvalue && (
                            <p className="mt-0.5 text-sm text-[var(--color-text-3)]">
                                {subvalue}
                            </p>
                        )}
                    </div>
                    {icon && (
                        <div className="shrink-0 text-[var(--color-text-3)]">
                            {icon}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
