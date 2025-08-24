"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Icon from "@/components/atoms/Icon";
import clsx from "clsx";

export type SearchBarProps = {
    placeholder?: string;
    defaultValue?: string;
    /** 遷移先の検索ページ（クエリ q を付与） */
    actionPath?: string; // default: "/search"
    size?: "sm" | "md";
    className?: string;
};

export default function SearchBar({
    placeholder = "Search tickers, companies, news…",
    defaultValue = "",
    actionPath = "/search",
    size = "md",
    className,
}: SearchBarProps) {
    const router = useRouter();
    const inputRef = useRef<HTMLInputElement>(null);
    const [value, setValue] = useState(defaultValue);

    // Cmd/Ctrl + K でフォーカス
    useEffect(() => {
        const onKey = (e: KeyboardEvent) => {
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
            e.preventDefault();
            inputRef.current?.focus();
        }
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, []);

    const paddings = size === "sm" ? "px-3 py-2" : "px-4 py-3";
    const textSize = size === "sm" ? "text-[13px]" : "text-sm";

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const q = value.trim();
        if (!q) return;
        router.push(`${actionPath}?q=${encodeURIComponent(q)}`); // ← SPA遷移
    };

    return (
        <form
        onSubmit={handleSubmit}
        role="search"
        aria-label="Site search"
        className={clsx(
            "group flex w-full items-center rounded-full border transition-colors duration-200",
            paddings,
            textSize,
            // ガラス風 + フォーカスで明るく
            "bg-[var(--color-surface-1)]/60 border-white/10",
            "focus-within:bg-[var(--color-surface-2)]/70 focus-within:border-white/20",
            className
        )}
        >
        <Icon name="search" size={18} className="mr-3 shrink-0 text-[var(--color-text-3)]" />
        <input
            ref={inputRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={placeholder}
            className={clsx(
            "min-w-0 flex-1 bg-transparent outline-none border-0",
            "text-[var(--color-text-2)] placeholder-[var(--color-text-3)]"
            )}
            aria-label="Search query"
        />
        {/* Enterで送信 */}
        <button type="submit" className="sr-only">Search</button>
        </form>
    );
}