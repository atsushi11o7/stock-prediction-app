// src/components/organisms/Sidebar/Sidebar.tsx
"use client";

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
    /** ロゴ/検索/ナビの“共通の見た目幅”(px) */
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
    const contentStyle = { width: "100%", maxWidth: contentWidth };

    return (
        <aside
            style={{ width }}
            className={clsx(
                "flex h-dvh flex-col bg-[var(--color-panel)] border-r border-white/10",
                className
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
    );
}