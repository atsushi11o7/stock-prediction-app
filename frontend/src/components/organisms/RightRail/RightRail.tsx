"use client";

import clsx from "clsx";

export type RightRailProps = {
    /** 上下左右の内側余白 */
    paddingClass?: string;    // 例: "px-4 py-5"
    className?: string;
    children?: React.ReactNode;
};

export default function RightRail({
    paddingClass = "px-4 py-5",
    className,
    children,
}: RightRailProps) {
    return (
        <aside
            className={clsx(
                // モバイル・タブレット: mainの下に表示（通常のブロック要素）
                // デスクトップ: グリッドの右カラム
                "flex flex-col",
                "border-t lg:border-t-0 lg:border-l border-white/10 bg-[var(--color-panel)]",
                paddingClass,
                className
            )}
        >
            <div className="flex flex-col gap-4">
                {children}
            </div>
        </aside>
    );
}