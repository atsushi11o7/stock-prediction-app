import type { Meta, StoryObj } from "@storybook/react";
import ForecastNote from "./ForecastNote";

const meta = {
    title: "Molecules/ForecastNote",
    component: ForecastNote,
    args: {
        title: "Model note",
        text: "生成AI投資とPCサイクル回復で上振れを想定。\n夏場に調整も、基調は右肩上がり。",
        arrowSide: "top",
        showArrow: true,
        maxWidth: 300,
    },
    argTypes: {
        arrowSide: { control: "inline-radio", options: ["top", "right", "bottom", "left"] },
        showArrow: { control: "boolean" },
        maxWidth: { control: { type: "number", min: 180, max: 480, step: 10 } },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
} satisfies Meta<typeof ForecastNote>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => (
        <div className="relative h-[220px] w-full rounded-2xl border border-white/10 bg-[var(--color-panel)] p-6">
            {/* モックの「チャート領域」 */}
            <div className="absolute inset-6 rounded-lg border border-white/10 bg-black/10" />
            <ForecastNote {...args} style={{ left: 40, top: 24 }} />
        </div>
    ),
};

export const ArrowSides: Story = {
    render: () => (
        <div className="relative grid h-[260px] w-full grid-cols-2 gap-4">
            <div className="relative rounded-2xl border border-white/10 bg-[var(--color-panel)]">
                <ForecastNote
                    title="Top"
                    text="上にテール"
                    arrowSide="top"
                    style={{ left: 24, top: 16 }}
                />
            </div>
            <div className="relative rounded-2xl border border-white/10 bg-[var(--color-panel)]">
                <ForecastNote
                    title="Right"
                    text="右にテール"
                    arrowSide="right"
                    style={{ right: 24, top: 16 }}
                />
            </div>
            <div className="relative rounded-2xl border border-white/10 bg-[var(--color-panel)]">
                <ForecastNote
                    title="Bottom"
                    text="下にテール"
                    arrowSide="bottom"
                    style={{ left: 24, bottom: 16 }}
                />
            </div>
            <div className="relative rounded-2xl border border-white/10 bg-[var(--color-panel)]">
                <ForecastNote
                    title="Left"
                    text="左にテール"
                    arrowSide="left"
                    style={{ left: 16, top: 16 }}
                />
            </div>
        </div>
    ),
};