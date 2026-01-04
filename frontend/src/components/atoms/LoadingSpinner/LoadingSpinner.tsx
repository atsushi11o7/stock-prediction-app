// src/components/atoms/LoadingSpinner/LoadingSpinner.tsx
"use client";

import React from "react";
import clsx from "clsx";

export type LoadingSpinnerProps = {
    /** Size of the spinner */
    size?: "sm" | "md" | "lg";
    /** Optional message to display below spinner */
    message?: string;
    /** Custom className */
    className?: string;
};

const SIZE = {
    sm: "w-4 h-4 border-2",
    md: "w-8 h-8 border-[3px]",
    lg: "w-12 h-12 border-4",
};

export default function LoadingSpinner({
    size = "md",
    message,
    className,
}: LoadingSpinnerProps) {
    return (
        <div className={clsx("flex flex-col items-center justify-center gap-3", className)}>
            <div
                className={clsx(
                    "rounded-full border-[var(--color-surface-2)] border-t-[var(--color-brand-500)] animate-spin",
                    SIZE[size]
                )}
                role="status"
                aria-label="Loading"
            />
            {message && (
                <p className="text-sm text-[var(--color-text-3)]">{message}</p>
            )}
        </div>
    );
}
