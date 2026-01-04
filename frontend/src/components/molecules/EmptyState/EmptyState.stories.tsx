// src/components/molecules/EmptyState/EmptyState.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs";
import { Search, TrendingUp, FileX } from "lucide-react";
import EmptyState from "./EmptyState";

const meta: Meta<typeof EmptyState> = {
    title: "Molecules/EmptyState",
    component: EmptyState,
    args: {
        title: "データがありません",
        message: "表示するデータが見つかりませんでした。",
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof EmptyState>;

export const Default: Story = {};

export const WithAction: Story = {
    args: {
        title: "銘柄が見つかりません",
        message: "検索条件に一致する銘柄がありませんでした。",
        action: {
            label: "すべての銘柄を見る",
            href: "/stocks",
        },
    },
};

export const WithCustomIcon: Story = {
    args: {
        title: "検索結果なし",
        message: "検索キーワードに一致する銘柄が見つかりませんでした。別のキーワードで試してください。",
        icon: <Search className="w-12 h-12 text-[var(--color-text-3)]" />,
        action: {
            label: "銘柄一覧に戻る",
            href: "/stocks",
        },
    },
};

export const NoForecasts: Story = {
    args: {
        title: "予測データなし",
        message: "この銘柄の予測データはまだ生成されていません。",
        icon: <TrendingUp className="w-12 h-12 text-[var(--color-text-3)]" />,
    },
};

export const NoResults: Story = {
    args: {
        title: "該当する銘柄がありません",
        message: "スクリーニング条件を緩めて再度お試しください。",
        icon: <FileX className="w-12 h-12 text-[var(--color-text-3)]" />,
        action: {
            label: "条件をリセット",
            href: "/screening",
        },
    },
};
