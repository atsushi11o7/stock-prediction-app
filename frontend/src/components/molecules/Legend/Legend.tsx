"use client";

import React from "react";
import clsx from "clsx";
import LineChip from "@/components/atoms/LineChip";

export type LegendItem = {
    color: string;
    label: string;
};

export type LegendProps = {
    /** 凡例アイテムの配列（色＋ラベル） */
    items: LegendItem[];
    /** 配置方向（横並び/縦並び） */
    direction?: "row" | "column";
    /** 折返し可否（row 時のみ使用） */
    wrap?: boolean;
    /** 間隔の密度 */
    density?: "sm" | "md";
    /** 左右の揃え（row のときに有効） */
    align?: "start" | "center" | "end" | "between";
    /** アクセシビリティ用ラベル */
    ariaLabel?: string;
    className?: string;
};

const GAP = {
    sm: "gap-2",
    md: "gap-3",
};

export default function Legend({
    items,
    direction = "row",
    wrap = true,
    density = "md",
    align = "start",
    ariaLabel = "Legend",
    className,
}: LegendProps) {
    return (
        <ul
            aria-label={ariaLabel}
            role="list"
            className={clsx(
                "m-0 p-0 list-none",
                direction === "row"
                    ? clsx(
                        "flex",
                        wrap ? "flex-wrap" : "flex-nowrap",
                        align === "start" && "justify-start",
                        align === "center" && "justify-center",
                        align === "end" && "justify-end",
                        align === "between" && "justify-between",
                        GAP[density]
                    )
                    : clsx("flex flex-col", GAP[density]),
                className
            )}
        >
            {items.map((it, i) => (
                <li key={`${it.label}-${i}`} role="listitem" className="m-0 p-0">
                    <LineChip color={it.color} label={it.label} />
                </li>
            ))}
        </ul>
    );
}