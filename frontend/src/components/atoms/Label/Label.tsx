"use client";

import React from "react";
import clsx from "clsx";

export type LabelProps = {
    children: React.ReactNode;
    /** 文字サイズ */
    size?: "xs" | "sm" | "md" | "lg";
    /** 色トーン */
    tone?: "primary" | "secondary" | "muted" | "brand" | "success" | "danger";
    /** 太さ */
    weight?: "normal" | "medium" | "semibold" | "bold";
    /** テキストの寄せ */
    align?: "left" | "center" | "right";
    /** 行間 */
    leading?: "tight" | "snug" | "normal";
    /** 大文字化 */
    uppercase?: boolean;
    /** 1行省略（ellipsis） */
    truncate?: boolean;
    /** 要素タイプ（デフォルト span） */
    as?: "span" | "p" | "div";
    className?: string;
};

const SIZE = {
    xs: "text-[11px]",
    sm: "text-[13px]",
    md: "text-sm",
    lg: "text-base",
} as const;

const TONE = {
    primary: "text-[var(--color-text-1)]",
    secondary: "text-[var(--color-text-2)]",
    muted: "text-[var(--color-text-3)]",
    brand: "text-[var(--color-brand-600)]",
    success: "text-[var(--color-success)]",
    danger: "text-[var(--color-danger)]",
} as const;

const WEIGHT = {
    normal: "font-normal",
    medium: "font-medium",
    semibold: "font-semibold",
    bold: "font-bold",
} as const;

const LEADING = {
    tight: "leading-tight",
    snug: "leading-snug",
    normal: "leading-normal",
} as const;

export default function Label({
    children,
    size = "sm",
    tone = "secondary",
    weight = "normal",
    align = "left",
    leading = "normal",
    uppercase = false,
    truncate = false,
    as: Tag = "span",
    className,
}: LabelProps) {
    return (
        <Tag
            className={clsx(
                "select-none",
                SIZE[size],
                TONE[tone],
                WEIGHT[weight],
                LEADING[leading],
                {
                    "text-left": align === "left",
                    "text-center": align === "center",
                    "text-right": align === "right",
                    uppercase,
                    "truncate": truncate,
                },
                className
            )}
        >
            {children}
        </Tag>
    );
}