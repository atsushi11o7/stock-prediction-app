import React from "react";
import type { Meta, StoryObj } from "@storybook/react";
import LineSeries, { type LineSeriesProps, type Series } from "./LineSeries";

/** --- ストーリー内ユーティリティ --------------------------------------- */

// SVG サイズとパディング（簡易レイアウト）
const WIDTH = 720;
const HEIGHT = 260;
const PADDING = { top: 16, right: 16, bottom: 24, left: 40 };

const plotX1 = PADDING.left;
const plotY1 = PADDING.top;
const plotX2 = WIDTH - PADDING.right;
const plotY2 = HEIGHT - PADDING.bottom;

// デモ用データ（ギャップ入り）
const DEFAULT_SERIES: Series = [
    120, 121, 122, 125, null, 126, 124, 128, 130, 129, 133, 131, 134, 137, 139, 138, 141, 145,
];

function extentFrom(series: Series): [number, number] {
    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;
    for (const v of series) {
        if (v == null || !Number.isFinite(v)) continue;
        if (v < min) min = v;
        if (v > max) max = v;
    }
    if (!Number.isFinite(min) || !Number.isFinite(max)) return [0, 1];
    if (min === max) return [min - 1, max + 1];
    return [min, max];
}

const [YMIN, YMAX] = extentFrom(DEFAULT_SERIES);

const X_OF: LineSeriesProps["xOf"] = (i) => {
    const n = DEFAULT_SERIES.length;
    const t = n <= 1 ? 0 : i / (n - 1);
    return plotX1 + (plotX2 - plotX1) * t;
};

const Y_OF: LineSeriesProps["yOf"] = (v) => {
    const t = (v - YMIN) / (YMAX - YMIN);
    // SVG は下が正方向なので上下反転
    return plotY2 - (plotY2 - plotY1) * t;
};

// 背景グリッド（簡易）
function Grid() {
    const cols = 6;
    const rows = 3;
    const vx: number[] = [];
    const vy: number[] = [];
    for (let c = 0; c <= cols; c++) {
        const x = plotX1 + ((plotX2 - plotX1) * c) / cols;
        vx.push(x);
    }
    for (let r = 0; r <= rows; r++) {
        const y = plotY1 + ((plotY2 - plotY1) * r) / rows;
        vy.push(y);
    }
    return (
        <g opacity={0.25} stroke="currentColor">
            {vx.map((x, i) => (
                <line key={`vx-${i}`} x1={x} x2={x} y1={plotY1} y2={plotY2} strokeDasharray="4 6" />
            ))}
            {vy.map((y, i) => (
                <line key={`vy-${i}`} x1={plotX1} x2={plotX2} y1={y} y2={y} strokeDasharray="4 6" />
            ))}
        </g>
    );
}

/** --- Meta ---------------------------------------------------------------- */

const meta: Meta<typeof LineSeries> = {
    title: "Molecules/LineSeries",
    component: LineSeries,
    args: {
        series: DEFAULT_SERIES,
        xOf: X_OF,
        yOf: Y_OF,
        stroke: "var(--color-brand-600)",
        strokeWidth: 3,
        opacity: 1,
        dash: null,
        strokeLinecap: "round",
        strokeLinejoin: "round",
        glow: false,
        glowWidth: 10,
        glowOpacity: 0.35,
        animateDraw: false,
        durationMs: 1200,
        delayMs: 0,
        clip: { x1: plotX1, y1: plotY1, x2: plotX2, y2: plotY2 },
    },
    argTypes: {
        series: { control: false }, // 縦軸スケーリングを簡単にするため固定
        xOf: { control: false },
        yOf: { control: false },
        clip: { control: false },
        stroke: { control: "color" },
        strokeWidth: { control: { type: "number", min: 1, max: 10, step: 1 } },
        opacity: { control: { type: "number", min: 0, max: 1, step: 0.05 } },
        dash: { control: "text" },
        glow: { control: "boolean" },
        glowWidth: { control: { type: "number", min: 2, max: 24, step: 1 } },
        glowOpacity: { control: { type: "number", min: 0, max: 1, step: 0.05 } },
        animateDraw: { control: "boolean" },
        durationMs: { control: { type: "number", min: 200, max: 5000, step: 100 } },
        delayMs: { control: { type: "number", min: 0, max: 3000, step: 50 } },
        strokeLinecap: { control: "inline-radio", options: ["butt", "round", "square"] },
        strokeLinejoin: { control: "inline-radio", options: ["miter", "round", "bevel"] },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof meta>;

/** --- 共通レンダラ：SVG キャンバスに LineSeries を載せる ------------------ */
function Frame(props: LineSeriesProps) {
    return (
        <svg width={WIDTH} height={HEIGHT} style={{ color: "rgba(255,255,255,0.6)" }}>
            <rect
                x={0}
                y={0}
                width={WIDTH}
                height={HEIGHT}
                fill="var(--color-panel, #121217)"
                stroke="rgba(255,255,255,0.1)"
            />
            <Grid />
            <LineSeries {...props} />
        </svg>
    );
}

/** --- Stories -------------------------------------------------------------- */

export const Default: Story = {
    render: (args) => <Frame {...args} />,
};

export const Dashed: Story = {
    name: "Dashed（点線）",
    args: { dash: "6 6" },
    render: (args) => <Frame {...args} />,
};

export const Glow: Story = {
    name: "Glow（やわらかい外側グロー）",
    args: {
        glow: true,
        glowWidth: 12,
        glowOpacity: 0.35,
        stroke: "#6DDB5E",
    },
    render: (args) => <Frame {...args} />,
};

export const AnimateDraw: Story = {
    name: "Draw Animation（左→右に描画）",
    args: {
        animateDraw: true,
        durationMs: 1400,
        delayMs: 200,
        stroke: "var(--color-brand-600)",
    },
    render: (args) => <Frame {...args} />,
};

export const ThickPurple: Story = {
    name: "Thick Purple",
    args: { stroke: "var(--color-brand-700)", strokeWidth: 5 },
    render: (args) => <Frame {...args} />,
};