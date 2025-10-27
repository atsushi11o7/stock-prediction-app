import type { Meta, StoryObj } from "@storybook/react";
import SplitMarker from "./SplitMarker";

const meta = {
    title: "Molecules/SplitMarker",
    component: SplitMarker,
    args: {
        x: 420,
        y1: 40,
        y2: 300,
        stroke: "var(--color-brand-600)",
        strokeWidth: 2,
        dash: "6 6",
        opacity: 0.9,
        showDot: true,
        dotRadius: 3,
        showLabel: true,
        label: "Forecast start",
        labelSide: "top",
        labelOffset: 8,
        clip: { x1: 40, y1: 20, x2: 780, y2: 320 },
    },
    argTypes: {
        labelSide: { control: "inline-radio", options: ["top", "right", "bottom", "left"] },
        strokeWidth: { control: { type: "number", min: 1, max: 6, step: 0.5 } },
        opacity: { control: { type: "number", min: 0, max: 1, step: 0.05 } },
        dash: { control: "text" },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
} satisfies Meta<typeof SplitMarker>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => (
        <svg width={820} height={360} className="rounded-2xl border border-white/10 bg-[var(--color-panel)]">
            {/* プロット枠 */}
            <rect
                x={args.clip!.x1}
                y={args.clip!.y1}
                width={args.clip!.x2 - args.clip!.x1}
                height={args.clip!.y2 - args.clip!.y1}
                fill="none"
                stroke="rgba(255,255,255,0.14)"
            />
            <SplitMarker {...args} />
        </svg>
    ),
};

export const LabelSides: Story = {
    render: (args) => (
        <svg width={820} height={360} className="rounded-2xl border border-white/10 bg-[var(--color-panel)]">
            <rect
                x={40}
                y={20}
                width={780 - 40}
                height={320 - 20}
                fill="none"
                stroke="rgba(255,255,255,0.14)"
            />
            <SplitMarker {...args} x={180} labelSide="left" label="as of 2022-01" />
            <SplitMarker {...args} x={340} labelSide="top" label="as of 2023-01" />
            <SplitMarker {...args} x={500} labelSide="right" label="as of 2024-01" />
            <SplitMarker {...args} x={660} labelSide="bottom" label="as of 2025-01" />
        </svg>
    ),
};