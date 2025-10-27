"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Icon, { type IconName } from "@/components/atoms/Icon";
import clsx from "clsx";

export type NavItemProps = {
    href: string;
    label: string;
    icon: IconName;
    size?: "sm" | "md";
    variant?: "pill" | "glass";
};

export default function NavItem({
    href,
    label,
    icon,
    size = "md",
    variant = "pill",
}: NavItemProps) {
    const pathname = usePathname();
    const active =
        href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(href + "/");

    const paddings = size === "sm" ? "px-3 py-2" : "px-4 py-3";
    const textSize = size === "sm" ? "text-[13px]" : "text-sm";
    const iconPx   = size === "sm" ? 18 : 20;
    const gap      = size === "sm" ? "gap-3.5" : "gap-4";

    // カラーパレットは globals.css の CSS 変数を使用
    const base =
        "block w-full rounded-full no-underline transition-colors duration-200 " +
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-brand-600)] " +
        "border";  // ここで常に border を確保（高さの揺れを防ぐ）


    const look =
        variant === "pill"
        ? active
            ? "bg-[var(--color-brand-600)] text-[var(--color-text-1)] border-transparent shadow-sm"
            : "bg-[var(--color-surface-1)]/70 text-[var(--color-text-2)] hover:bg-[var(--color-surface-2)]/70 border-white/10"
        : // glass
            active
            ? "bg-[var(--color-brand-600)] text-[var(--color-text-1)] border-transparent"
            : "bg-[var(--color-surface-1)]/40 text-[var(--color-text-2)] backdrop-blur-sm hover:bg-[var(--color-surface-2)]/60 border-white/10";

    return (
        <Link href={href} aria-current={active ? "page" : undefined}
        className={clsx(base, paddings, textSize, look)}
        >
        <span className={clsx("flex items-center", gap, "leading-[1] font-semibold")}>
            <Icon
            name={icon}
            size={iconPx}
            className="shrink-0 block text-current"  // block で baseline ギャップ排除
            strokeWidth={2}
            />
            <span className="block leading-[1]">{label}</span>
        </span>
        </Link>
    );
}