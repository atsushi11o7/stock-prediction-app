// src/components/organisms/Sidebar/Sidebar.tsx
"use client";

import { useState } from "react";
import Logo from "@/components/atoms/Logo";
import NavItem from "@/components/atoms/NavItem";
import SearchBar from "@/components/molecules/SearchBar";
import clsx from "clsx";

type Item = {
    href: string;
    label: string;
    icon: React.ComponentProps<typeof NavItem>["icon"];
};

export type SidebarProps = {
    /** サイドバーの外側幅(px) */
    width?: number;
    /** ロゴ/検索/ナビの"共通の見た目幅"(px) */
    contentWidth?: number;
    /** メインナビ */
    items?: Item[];
    /** 最下部の任意表示 */
    footerSlot?: React.ReactNode;
    className?: string;
};

const DEFAULT_ITEMS: Item[] = [
    { href: "/", label: "Home", icon: "home" },
    { href: "/stocks", label: "Stocks", icon: "lineChart" },
    { href: "/news", label: "News", icon: "newspaper" },
    { href: "/trends", label: "Trends", icon: "trendingUp" },
    { href: "/compare", label: "Compare", icon: "compare" },
];

export default function Sidebar({
    width = 268,          // 外側はややスリム
    contentWidth = 220,   // 中身の共通横幅（ロゴ/検索/ナビをこれで揃える）
    items = DEFAULT_ITEMS,
    footerSlot,
    className,
}: SidebarProps) {
    const [isOpen, setIsOpen] = useState(false);
    const contentStyle = { width: "100%", maxWidth: contentWidth };

    return (
        <>
            {/* ハンバーガーメニューボタン（モバイル・タブレットのみ表示） */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={clsx(
                    "fixed top-4 left-4 z-50 lg:hidden",
                    "w-14 h-14 rounded-2xl",
                    "bg-gradient-to-br from-[var(--color-surface-2)] to-[var(--color-surface-3)]",
                    "border border-white/20",
                    "flex items-center justify-center",
                    "hover:border-[var(--color-brand-500)] hover:shadow-lg hover:shadow-[var(--color-brand-500)]/20",
                    "transition-all duration-300",
                    "shadow-xl backdrop-blur-sm",
                    isOpen && "bg-gradient-to-br from-[var(--color-brand-500)] to-[var(--color-brand-600)]"
                )}
                aria-label="メニュー"
            >
                <div className="relative w-6 h-5 flex flex-col justify-center gap-1.5">
                    <span
                        className={clsx(
                            "block h-0.5 bg-white transition-all duration-300 origin-center",
                            isOpen ? "rotate-45 translate-y-2" : ""
                        )}
                    />
                    <span
                        className={clsx(
                            "block h-0.5 bg-white transition-all duration-300",
                            isOpen ? "opacity-0" : ""
                        )}
                    />
                    <span
                        className={clsx(
                            "block h-0.5 bg-white transition-all duration-300 origin-center",
                            isOpen ? "-rotate-45 -translate-y-2" : ""
                        )}
                    />
                </div>
            </button>

            {/* オーバーレイ（モバイル・タブレット時、メニュー開時のみ） */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                    onClick={() => setIsOpen(false)}
                />
            )}

            {/* サイドバー本体 */}
            <aside
                style={{ width }}
                className={clsx(
                    "flex h-screen flex-col bg-[var(--color-panel)] border-r border-white/10",
                    className,
                    // 常に固定位置
                    "fixed top-0 left-0 bottom-0 z-40 transition-transform duration-300",
                    // モバイル・タブレット: 左に隠す
                    isOpen ? "translate-x-0" : "-translate-x-full",
                    // デスクトップ: 常に表示
                    "lg:translate-x-0"
                )}
            >
            <div className="pt-6 pb-3">
                <div
                    className="mx-auto flex flex-col items-center space-y-6"
                    style={contentStyle}
                >
                    <div className="w-full flex justify-center">
                        <Logo width={contentWidth} />
                    </div>

                    <SearchBar size="md" />
                </div>
            </div>

            <nav className="flex-1 overflow-y-auto pb-4">
                <ul className="mx-auto space-y-3" style={contentStyle}>
                    {items.map((it) => (
                        <li key={it.href}>
                            {/* NavItem：ボタン自体は w-full で“同じ見た目幅”に */}
                            <NavItem
                                href={it.href}
                                label={it.label}
                                icon={it.icon}
                                size="md"
                            />
                        </li>
                    ))}
                </ul>
            </nav>

            {/* フッター */}
            <div className="border-t border-white/10 py-3 text-[12px] text-[var(--color-text-3)]">
                <div className="mx-auto" style={contentStyle}>
                    {footerSlot ?? <span>© FumiKabu</span>}
                </div>
            </div>
        </aside>
        </>
    );
}