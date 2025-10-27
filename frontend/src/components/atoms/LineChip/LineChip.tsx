"use client";

import React from "react";
import clsx from "clsx";

export type LineChipProps = {
    /** 凡例に表示する色 */
    color: string;
    /** テキストラベル */
    label: string;
    /** 追加のクラス名 */
    className?: string;
};

export default function LineChip({ color, label, className }: LineChipProps) {
    return (
        <span className={clsx("inline-flex items-center gap-2", className)}>
            {/* 色チップ（ラインの色を示す） */}
            <span
                className="block h-[10px] w-[20px] rounded-sm"
                style={{ backgroundColor: color }}
            />
            <span className="text-sm text-[var(--color-text-2)]">{label}</span>
        </span>
    );
}