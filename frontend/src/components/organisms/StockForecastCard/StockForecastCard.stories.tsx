import type { Meta, StoryObj } from "@storybook/nextjs";
import StockForecastCard, { type StockForecastCardProps } from "./StockForecastCard";
import type { StockForecastData } from "@/libs/chart/types";

/** 3年過去 + 1年未来（1M刻み）ダミーを生成 */
function makeMockData(): StockForecastData {
    const months = 48;                // 36 past + 12 future
    const past = 36;
    const predictStartIndex = past;

    // ラベル
    const labels: string[] = [];
    const base = new Date(2022, 0, 1);
    for (let i = 0; i < months; i++) {
        const d = new Date(base);
        d.setMonth(base.getMonth() + i);
        labels.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
    }

    // 実測
    const actual: (number | null)[] = Array.from({ length: months }, (_, i) => {
        if (i >= predictStartIndex) return null;
        const trend = 120 + i * 1.7;
        const noise = Math.sin(i / 3.1) * 2.4;
        return Math.round((trend + noise) * 10) / 10;
    });

    // 予測（現在から連続）
    const predicted: (number | null)[] = Array.from({ length: months }, (_, i) => {
        if (i < predictStartIndex) return null;
        const t = i - predictStartIndex;
        const start = actual[predictStartIndex - 1] ?? 150;
        const trend = start + t * 2.2;
        const noise = Math.sin((t + 0.6) / 2.2) * 2.0;
        return Math.round((trend + noise) * 10) / 10;
    });

    // 過去予測（長さ自由の例）
    const historicalPredictions = [
        {
            asOfIndex: 12,
            values: Array.from({ length: months }, (_, i) =>
                i < 12 || i >= predictStartIndex
                    ? null
                    : (actual[11]! + (i - 12) * 1.8 + Math.sin((i - 12) / 2.1) * 1.4)
            ),
        },
        {
            asOfIndex: 24,
            values: Array.from({ length: months }, (_, i) =>
                i < 24 || i >= 30
                    ? null
                    : (actual[23]! + (i - 24) * 1.6 + Math.sin((i - 24) / 1.9) * 1.1)
            ),
        },
    ];

    return {
        ticker: "NVDA",
        labels,
        actual,
        predicted,
        historicalPredictions,
        predictStartIndex,
        comment: "需要の底堅さが継続。短期は変動も、基調は上向き。",
    };
}

const meta: Meta<typeof StockForecastCard> = {
    title: "Organisms/StockForecastCard",
    component: StockForecastCard,
    args: {
        data: makeMockData(),
        title: "NVDA",
        subtitle: "NVIDIA Corporation — Semiconductors",
        tag: "Mock",
        metrics: [
            { label: "Price", value: "$128.4", tone: "neutral" },
            { label: "Change", value: "+1.2%", tone: "up" },
            { label: "PER", value: "42.1x", tone: "brand" },
            { label: "Sector", value: "Semiconductors", tone: "neutral" },
            { label: "PBR", value: "6.8x", tone: "brand" },
            { label: "配当利回り", value: "0.03%", tone: "neutral" },
            { label: "ROE", value: "28.4%", tone: "brand" },
            { label: "時価総額", value: "¥210兆", tone: "neutral" },
            { label: "出来高", value: "35.2M", tone: "neutral" },
            { label: "β", value: "1.25", tone: "neutral" },
            { label: "EPS成長率", value: "+18% YoY", tone: "up" },
            { label: "フリーCF", value: "¥1.2兆", tone: "neutral" },
            { label: "D/E", value: "0.35", tone: "neutral" },
        ],
        showLegend: true,
        chartProps: {
            width: 920,
            height: 420,
            showGrid: true,
            showSplit: true,
            showNote: true,
            anchorAtCurrent: true,
            historicalClipToNow: false,
            animate: true,
            colors: {
                actual: "var(--color-brand-600)",
                predicted: "#6DDB5E",
                predictedPast: "rgba(109,219,94,0.45)",
            },
        },
    } satisfies StockForecastCardProps,
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const NoLegend: Story = {
    name: "Legend なし",
    args: { showLegend: false },
};