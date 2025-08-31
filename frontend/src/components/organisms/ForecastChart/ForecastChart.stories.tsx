import type { Meta, StoryObj } from "@storybook/react";
import ForecastChart from "./ForecastChart";
import type { StockForecastData } from "@/libs/chart/types";

/**
 * モックデータ（1カ月刻み / 過去36 + 未来12 = 48点）
 * - 実測→予測の切替点で値が連続（段差なし）
 * - 過去予測は 2 本（2023-01, 2024-01）。長さ自由の例を混ぜたい場合は適宜追加
 */
function makeMockData(): StockForecastData {
    const months = 48;                // 2022-01 〜 2025-12
    const past = 36;                  // 2022-01 〜 2024-12 が実測
    const predictStartIndex = past;   // 2025-01 から未来予測

    // ラベル YYYY-MM
    const labels: string[] = [];
    const base = new Date(2022, 0, 1);
    for (let i = 0; i < months; i++) {
        const d = new Date(base);
        d.setMonth(base.getMonth() + i);
        labels.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
    }

    // 実測：右肩上がり + ノイズ（predictStartIndex 以降は null）
    const actual: (number | null)[] = Array.from({ length: months }, (_, i) => {
        if (i >= predictStartIndex) return null;
        const trend = 120 + i * 1.8;
        const noise = Math.sin(i / 3.2) * 2.5;
        return Math.round((trend + noise) * 10) / 10;
    });

    // 予測：先頭は実測の終点と一致（段差ゼロ）
    const predicted: (number | null)[] = Array.from({ length: months }, (_, i) => {
        if (i < predictStartIndex) return null;
        const t = i - predictStartIndex;
        const start = actual[predictStartIndex - 1] ?? 150;
        const trend = start + t * 2.2;
        const noise = Math.sin((t + 1.5) / 2.6) * 2.0;
        return Math.round((trend + noise) * 10) / 10;
    });

    // 過去予測（長さ自由の例も含めて3本）
    const historicalPredictions = [
        // asOf〜今まで（フルに近い）
        {
            asOfIndex: 12,
            values: Array.from({ length: months }, (_, i) =>
                i < 12 || i >= predictStartIndex
                    ? null
                    : (actual[11]! + (i - 12) * 1.9 + Math.sin((i - 12) / 2.4) * 1.8)
            ),
        },
        // 短め
        {
            asOfIndex: 24,
            values: Array.from({ length: months }, (_, i) =>
                i < 24 || i >= 30
                    ? null
                    : (actual[23]! + (i - 24) * 1.7 + Math.sin((i - 24) / 2.0) * 1.2)
            ),
        },
        // 長さ自由：実測の長さと同等のライン（未来には出さない）
        {
            asOfIndex: 0,
            values: Array.from({ length: months }, (_, i) =>
                i >= predictStartIndex ? null : (120 + i * 1.5 + Math.sin(i / 3) * 1.0)
            ),
        },
    ];

    const comment =
        "生成AI投資とデータセンター更新が需要を牽引。短期調整があっても基調は上向き。";

    return {
        ticker: "NVDA",
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
        padding: { top: 20, right: 16, bottom: 48, left: 56 },
        showGrid: true,
        gridRows: 3,
        gridCols: 6,
        gridDash: null,
        showSplit: true,
        splitLabel: "Forecast start",
        showNote: true,
        showTickerLabel: true,
        historicalClipToNow: false,  // ← 長さ自由の表示をデフォルトに
        anchorAtCurrent: true,       // ← “現在アンカー” 有効
        showJoinSegment: false,      // ← アンカーがあるので既定は不要
        colors: {
            actual: "var(--color-brand-600)",
            predicted: "#6DDB5E",
            predictedPast: "rgba(109,219,94,0.45)",
        },
    },
    argTypes: {
        showGrid: { control: "boolean" },
        gridRows: { control: { type: "number", min: 0, max: 12, step: 1 } },
        gridCols: { control: { type: "number", min: 0, max: 24, step: 1 } },
        gridDash: { control: "text" },
        showSplit: { control: "boolean" },
        showNote: { control: "boolean" },
        showTickerLabel: { control: "boolean" },
        historicalClipToNow: { control: "boolean" },
        anchorAtCurrent: { control: "boolean" },
        showJoinSegment: { control: "boolean" },
        width: { control: { type: "number", min: 600, max: 1400, step: 20 } },
        height: { control: { type: "number", min: 360, max: 720, step: 10 } },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const ClipHistoricalToNow: Story = {
    name: "過去予測を“今まで”にクリップ",
    args: { historicalClipToNow: true },
};

export const NoAnchor_ShowJoin: Story = {
    name: "アンカー無効 + 接続線ON（ギャップ確認用）",
    args: { anchorAtCurrent: false, showJoinSegment: true },
};

export const Compact: Story = {
    name: "小さめサイズ",
    args: { width: 760, height: 420 },
};