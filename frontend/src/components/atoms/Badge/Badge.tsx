"use client";

import React from "react";
import clsx from "clsx";

export type BadgeProps = {
    children: React.ReactNode;
    tone?: "brand" | "success" | "danger" | "muted";
    size?: "sm" | "md";
    rounded?: "sm" | "md" | "full";
    className?: string;
};

const SIZE = {
    sm: "text-[11px] px-2 py-[2px]",
    md: "text-xs px-2.5 py-1",
};

const ROUNDED = {
    sm: "rounded",
    md: "rounded-md",
    full: "rounded-full",
};

const TONE = {
    brand:   "bg-[var(--color-brand-600)] text-white",
    success: "bg-[var(--color-success)] text-white",
    danger:  "bg-[var(--color-danger)] text-white",
    muted:   "bg-[var(--color-surface-2)] text-[var(--color-text-2)]",
};

export default function Badge({
    children,
    tone = "brand",
    size = "md",
    rounded = "full",
    className,
}: BadgeProps) {
    return (
        <span
            className={clsx(
                "inline-flex items-center font-medium select-none",
                SIZE[size],
                ROUNDED[rounded],
                TONE[tone],
                className
            )}
        >
            {children}
        </span>
    );
}