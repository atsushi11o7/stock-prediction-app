// src/components/molecules/EmptyState/EmptyState.tsx
"use client";

import React from "react";
import clsx from "clsx";
import Link from "next/link";
import { Inbox } from "lucide-react";

export type EmptyStateProps = {
    /** Title of the empty state */
    title: string;
    /** Description message */
    message: string;
    /** Optional icon to display */
    icon?: React.ReactNode;
    /** Optional action link */
    action?: {
        label: string;
        href: string;
    };
    /** Custom className */
    className?: string;
};

export default function EmptyState({
    title,
    message,
    icon,
    action,
    className,
}: EmptyStateProps) {
    const defaultIcon = <Inbox className="w-12 h-12 text-[var(--color-text-3)]" />;

    return (
        <div
            className={clsx(
                "rounded-2xl border border-white/10 bg-[var(--color-panel)]",
                "p-12 text-center",
                className
            )}
        >
            <div className="flex flex-col items-center gap-4 max-w-md mx-auto">
                <div className="flex items-center justify-center w-16 h-16 rounded-full bg-[var(--color-surface-1)]">
                    {icon ?? defaultIcon}
                </div>

                <div>
                    <h3 className="text-lg font-semibold text-[var(--color-text-1)]">
                        {title}
                    </h3>
                    <p className="mt-2 text-sm text-[var(--color-text-3)]">
                        {message}
                    </p>
                </div>

                {action && (
                    <Link
                        href={action.href}
                        className={clsx(
                            "mt-2 px-4 py-2 rounded-lg",
                            "bg-[var(--color-brand-600)] hover:bg-[var(--color-brand-700)]",
                            "text-sm font-medium text-white",
                            "transition-colors"
                        )}
                    >
                        {action.label}
                    </Link>
                )}
            </div>
        </div>
    );
}
