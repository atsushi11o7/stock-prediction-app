"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import clsx from "clsx";

export type SeeAllCardProps = {
    href: string;
    label?: string;
    className?: string;
};

export default function SeeAllCard({
    href,
    label = "株価一覧へ",
    className,
}: SeeAllCardProps) {
    return (
        <Link
            href={href}
            className={clsx(
                "flex items-center justify-center rounded-2xl border border-white/10",
                "bg-[var(--color-surface-1)] hover:bg-[var(--color-surface-2)] transition-colors",
                "min-h-[var(--scroll-card-h,88px)] min-w-[120px] px-3",
                className
            )}
        >
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--color-text-2)]">
                {label}
                <ArrowRight size={14} className="text-[var(--color-text-3)]" />
            </span>
        </Link>
    );
}