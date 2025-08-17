"use client";

import Link from "next/link";

export type LogoProps = {
    /* 表示幅(px)、高さは自動でアスペクト比維持 */
    width?: number;
};

const LOGO_SRC = "/brand/fumikabu_logo.svg";

export default function Logo({ width = 200 }: LogoProps) {
    return (
        <Link
        href="/"
        aria-label="ホームへ戻る"
        className="inline-flex items-center no-underline text-inherit"
        >
            <img
                src={LOGO_SRC}
                alt="FumiKabu ロゴ"
                style={{ width, height: "auto" }}
                draggable={false}
            />
        </Link>
    );
}