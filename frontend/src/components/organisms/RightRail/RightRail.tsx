"use client";

import clsx from "clsx";

export type RightRailProps = {
    /** 右レールの固定幅(px) */
    width?: number;           // 例: 320
    /** 上下左右の内側余白 */
    paddingClass?: string;    // 例: "px-4 py-5"
    className?: string;
    children?: React.ReactNode; // ← 差し込み
};

export default function RightRail({
    width = 320,
    paddingClass = "px-4 py-5",
    className,
    children,
}: RightRailProps) {
    return (
        <aside
            style={{ width }}
            className={clsx(
                "border-l border-white/10 bg-[var(--color-panel)]",
                "flex flex-col gap-4 overflow-y-auto",
                paddingClass,
                className
            )}
        >
            {children}
        </aside>
    );
}