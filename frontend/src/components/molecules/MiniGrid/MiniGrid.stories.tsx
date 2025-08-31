import type { Meta, StoryObj } from "@storybook/react";
import MiniGrid from "./MiniGrid";

const meta = {
    title: "Molecules/MiniGrid",
    component: MiniGrid,
    args: {
        x1: 40,
        y1: 20,
        x2: 760,
        y2: 300,
        rows: 3,
        cols: 6,
        strokeWidth: 1,
        opacity: 0.28,
        dash: null,
        showBorder: false,
    },
    argTypes: {
        rows: { control: { type: "number", min: 0, max: 12, step: 1 } },
        cols: { control: { type: "number", min: 0, max: 24, step: 1 } },
        strokeWidth: { control: { type: "number", min: 0.5, max: 3, step: 0.5 } },
        opacity: { control: { type: "number", min: 0, max: 1, step: 0.05 } },
        dash: { control: "text" },
        showBorder: { control: "boolean" },
        stroke: { control: "color" },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
} satisfies Meta<typeof MiniGrid>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => (
        <svg
            width={820}
            height={360}
            className="rounded-2xl border border-white/10 bg-[var(--color-panel)]"
        >
            {/* プロット領域の目安 */}
            <rect
                x={args.x1}
                y={args.y1}
                width={args.x2 - args.x1}
                height={args.y2 - args.y1}
                fill="none"
                stroke="rgba(255,255,255,0.14)"
            />
            <MiniGrid {...args} />
        </svg>
    ),
};

export const DashedDense: Story = {
    args: { rows: 6, cols: 12, dash: "4 4", opacity: 0.22 },
    render: (args) => (
        <svg
            width={820}
            height={360}
            className="rounded-2xl border border-white/10 bg-[var(--color-panel)]"
        >
            <rect
                x={args.x1}
                y={args.y1}
                width={args.x2 - args.x1}
                height={args.y2 - args.y1}
                fill="none"
                stroke="rgba(255,255,255,0.14)"
            />
            <MiniGrid {...args} />
        </svg>
    ),
};

export const BorderVisible: Story = {
    args: { showBorder: true },
    render: (args) => (
        <svg
            width={820}
            height={360}
            className="rounded-2xl border border-white/10 bg-[var(--color-panel)]"
        >
            <MiniGrid {...args} />
        </svg>
    ),
};