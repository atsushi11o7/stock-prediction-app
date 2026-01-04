import type { Metadata } from "next";
import { Geist, Geist_Mono, Noto_Sans_JP } from "next/font/google";
import "./globals.css";

import Sidebar from "@/components/organisms/Sidebar";

const notoSansJp = Noto_Sans_JP({
    variable: "--font-noto-sans-jp",
    display: "swap",
    preload: false,
    weight: ["400", "700"],
});

const geistMono = Geist_Mono({
    variable: "--font-geist-mono",
    subsets: ["latin"],
});

export const metadata: Metadata = {
    title: "FumiKabu",
    description: "株価予測アプリ",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="ja" className={`${notoSansJp.variable} ${geistMono.variable}`}>
            <body className="bg-[var(--color-background)] text-[var(--color-text-1)]">
                {/* Sidebarコンポーネント（内部でハンバーガーメニュー機能を持つ） */}
                <Sidebar />

                {/* メインコンテンツエリア - デスクトップではサイドバー幅分を左にマージン */}
                <div className="lg:pl-[268px] min-h-dvh">
                    {children}
                </div>
            </body>
        </html>
    );
}