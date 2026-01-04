// src/components/molecules/ErrorCard/ErrorCard.tsx
"use client";

import React from "react";
import clsx from "clsx";
import { AlertCircle } from "lucide-react";

export type ErrorCardProps = {
    /** Error title */
    title?: string;
    /** Error message */
    message: string;
    /** Optional retry callback */
    retry?: () => void;
    /** Custom className */
    className?: string;
};

export default function ErrorCard({
    title = "エラーが発生しました",
    message,
    retry,
    className,
}: ErrorCardProps) {
    return (
        <div
            className={clsx(
                "rounded-2xl border border-red-500/20 bg-red-500/5",
                "p-6 text-center",
                className
            )}
            role="alert"
        >
            <div className="flex flex-col items-center gap-3">
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-red-500/10">
                    <AlertCircle className="w-6 h-6 text-red-400" />
                </div>

                <div>
                    <h3 className="text-lg font-semibold text-[var(--color-text-1)]">
                        {title}
                    </h3>
                    <p className="mt-1 text-sm text-[var(--color-text-3)]">
                        {message}
                    </p>
                </div>

                {retry && (
                    <button
                        onClick={retry}
                        className={clsx(
                            "mt-2 px-4 py-2 rounded-lg",
                            "bg-[var(--color-surface-1)] hover:bg-[var(--color-surface-2)]",
                            "border border-white/10",
                            "text-sm font-medium text-[var(--color-text-1)]",
                            "transition-colors"
                        )}
                    >
                        再試行
                    </button>
                )}
            </div>
        </div>
    );
}
