// src/components/molecules/ErrorCard/ErrorCard.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs";
import ErrorCard from "./ErrorCard";

const meta: Meta<typeof ErrorCard> = {
    title: "Molecules/ErrorCard",
    component: ErrorCard,
    args: {
        message: "データの取得に失敗しました。",
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof ErrorCard>;

export const Default: Story = {};

export const WithRetry: Story = {
    args: {
        message: "APIへの接続に失敗しました。",
        retry: () => alert("再試行中..."),
    },
};

export const CustomTitle: Story = {
    args: {
        title: "ネットワークエラー",
        message: "インターネット接続を確認してください。",
        retry: () => alert("再試行中..."),
    },
};

export const APIError: Story = {
    args: {
        title: "APIエラー",
        message: "銘柄データの取得に失敗しました。しばらく時間をおいてから再度お試しください。",
        retry: () => alert("再試行中..."),
    },
};

export const InCard: Story = {
    render: () => (
        <div className="max-w-2xl">
            <div className="rounded-2xl border border-white/10 bg-[var(--color-panel)] p-6">
                <h2 className="text-xl font-bold mb-4">株価予測チャート</h2>
                <ErrorCard
                    message="予測データの読み込みに失敗しました。"
                    retry={() => alert("再試行中...")}
                />
            </div>
        </div>
    ),
};
