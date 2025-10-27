import type { Meta, StoryObj } from "@storybook/react";
import ForecastChart from "./ForecastChart";
import type { StockForecastData } from "@/libs/chart/types";

/** モック：過去36 + 未来12 = 48点（1M刻み） */
function makeMockData(): StockForecastData {
    const months = 48;
    const past = 36;
    const predictStartIndex = past;

    const labels: string[] = [];
    const base = new Date(2022, 0, 1);
    for (let i = 0; i < months; i++) {
        const d = new Date(base);
        d.setMonth(base.getMonth() + i);
        labels.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
    }

    const actual: (number | null)[] = Array.from({ length: months }, (_, i) => {
        if (i >= predictStartIndex) return null;
        const trend = 12000 + i * 180; // 円のスケール例
        const noise = Math.sin(i / 3.2) * 220;
        return Math.round(trend + noise);
    });

    const predicted: (number | null)[] = Array.from({ length: months }, (_, i) => {
        if (i < predictStartIndex) return null;
        const t = i - predictStartIndex;
        const start = actual[predictStartIndex - 1] ?? 15000;
        const trend = start + t * 210;
        const noise = Math.sin((t + 1.5) / 2.6) * 180;
        return Math.round(trend + noise);
    });

    const historicalPredictions = [
        {
            asOfIndex: 12,
            values: Array.from({ length: months }, (_, i) =>
                i < 12 || i >= predictStartIndex
                    ? null
                    : Math.round((actual[11]! + (i - 12) * 190 + Math.sin((i - 12) / 2.4) * 160))
            ),
        },
        {
            asOfIndex: 24,
            values: Array.from({ length: months }, (_, i) =>
                i < 24 || i >= 30
                    ? null
                    : Math.round((actual[23]! + (i - 24) * 170 + Math.sin((i - 24) / 2.0) * 120))
            ),
        },
    ];

    const comment = "半導体部材の需要回復。為替の追い風も寄与。";

    return {
        ticker: "7203.T",
        labels,
        actual,
        predicted,
        historicalPredictions,
        predictStartIndex,
        comment,
    };
}

const meta: Meta<typeof ForecastChart> = {
    title: "Organisms/ForecastChart",
    component: ForecastChart,
    args: {
        data: makeMockData(),
        width: 920,
        height: 460,
        padding: { top: 20, right: 16, bottom: 52, left: 68 }, // 軸ラベル分だけ少し広げる

        showGrid: true,
        gridRows: 3,
        gridCols: 6,
        gridDash: null,

        showSplit: true,
        splitLabel: "Forecast start",
        showNote: true,
        showTickerLabel: true,

        historicalClipToNow: false,
        anchorAtCurrent: true,

        animate: true,
        durations: { revealTotalMs: 2200, fadeMs: 450, afterRevealDelayMs: 220 },

        colors: {
            actual: "var(--color-brand-600)",
            predicted: "#37C96B",
            predictedPast: "rgba(55,201,107,0.45)",
        },

        showAxes: true,
        yTickCount: 5,
        xMaxTicks: 8,
        // フォーマッタ（例：YYYY-MM → YY/MM にしたい場合の置き換え）
        // xFormatter: (lab) => {
        //     const [yy, mm] = lab.split("-");
        //     return `${yy.slice(2)}/${mm}`;
        // },
    },
    argTypes: {
        showAxes: { control: "boolean" },
        yTickCount: { control: { type: "number", min: 2, max: 10, step: 1 } },
        xMaxTicks: { control: { type: "number", min: 3, max: 12, step: 1 } },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const NoAxes: Story = {
    name: "軸なし",
    args: { showAxes: false, padding: { top: 20, right: 16, bottom: 48, left: 56 } },
};