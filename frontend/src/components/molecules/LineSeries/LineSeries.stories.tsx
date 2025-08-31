import type { Meta, StoryObj } from "@storybook/react";
import LineSeries from "./LineSeries";
import { createLinear, niceDomain } from "@/libs/chart/scale";

// --- 型要件を満たすためのダミー args（render内で上書きします） ---
const meta = {
    title: "Molecules/LineSeries",
    component: LineSeries,
    args: {
        series: [0, 1],                     // ダミー（renderで置き換え）
        xOf: (i: number) => i,              // ダミー（renderで置き換え）
        yOf: (v: number) => v,              // ダミー（renderで置き換え）
        stroke: "var(--color-brand-600)",
        strokeWidth: 3,
        opacity: 1,
        strokeLinecap: "round",
        strokeLinejoin: "round",
        dash: null,
        glow: false,
        glowOpacity: 0.5,
        glowWidth: 8,
        clip: null,
        ariaHidden: true,
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
} satisfies Meta<typeof LineSeries>;

export default meta;
type Story = StoryObj<typeof meta>;

// ダミーデータ（null でギャップを作る）
const baseSeries: (number | null)[] = [
    100, 102, 104, 106, 110, 112, 108, 109, 111, 115, 118, 122,
    126, 128, 130, null, null, 138, 140, 145, 150, 155, 160,
];

export const Default: Story = {
    render: (args) => {
        const series = baseSeries;
        const n = series.length;
        const W = 820, H = 360;
        const PAD = { l: 40, r: 20, t: 20, b: 40 };
        const plot = { x1: PAD.l, y1: PAD.t, x2: W - PAD.r, y2: H - PAD.b };

        const x = createLinear([0, n - 1], [plot.x1, plot.x2]);
        const [min, max] = niceDomain([100, 165], 4);
        const y = createLinear([min, max], [plot.y2, plot.y1]);

        return (
            <svg width={W} height={H} className="rounded-2xl border border-white/10 bg-[var(--color-panel)]">
                <rect
                    x={plot.x1}
                    y={plot.y1}
                    width={plot.x2 - plot.x1}
                    height={plot.y2 - plot.y1}
                    fill="none"
                    stroke="rgba(255,255,255,0.14)"
                />
                <LineSeries
                    {...args}
                    series={series}
                    xOf={(i) => x(i)}
                    yOf={(v) => y(v)}
                    clip={plot}
                />
            </svg>
        );
    },
};

export const DashedWithGlow: Story = {
    render: (args) => {
        const series = baseSeries;
        const n = series.length;
        const W = 820, H = 360;
        const PAD = { l: 40, r: 20, t: 20, b: 40 };
        const plot = { x1: PAD.l, y1: PAD.t, x2: W - PAD.r, y2: H - PAD.b };

        const x = createLinear([0, n - 1], [plot.x1, plot.x2]);
        const [min, max] = niceDomain([100, 165], 4);
        const y = createLinear([min, max], [plot.y2, plot.y1]);

        return (
            <svg width={W} height={H} className="rounded-2xl border border-white/10 bg-[var(--color-panel)]">
                <rect
                    x={plot.x1}
                    y={plot.y1}
                    width={plot.x2 - plot.x1}
                    height={plot.y2 - plot.y1}
                    fill="none"
                    stroke="rgba(255,255,255,0.14)"
                />
                <LineSeries
                    {...args}
                    series={series}
                    xOf={(i) => x(i)}
                    yOf={(v) => y(v)}
                    stroke="#6DDB5E"
                    dash="6 6"
                    glow
                    glowOpacity={0.35}
                    glowWidth={10}
                    clip={plot}
                />
            </svg>
        );
    },
};