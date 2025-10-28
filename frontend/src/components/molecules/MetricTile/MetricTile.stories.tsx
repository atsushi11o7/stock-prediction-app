import type { Meta, StoryObj } from "@storybook/nextjs";
import MetricTile from "./MetricTile";

const meta: Meta<typeof MetricTile> = {
    title: "Molecules/MetricTile",
    component: MetricTile,
    args: {
        title: "PER (P/E)",
        value: "25.4",
        hint: "TTM",
        tone: "neutral",
    },
    argTypes: {
        tone: { control: "inline-radio", options: ["neutral", "up", "down", "brand"] },
        compact: { control: "boolean" },
        align: { control: "inline-radio", options: ["left", "center", "right"] },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithUp: Story = {
    args: { title: "Change (1D)", value: "+2.1%", tone: "up" },
};

export const WithDown: Story = {
    args: { title: "Change (1D)", value: "-1.2%", tone: "down" },
};

export const Brand: Story = {
    args: { title: "Model Score", value: "A-", tone: "brand" },
};

export const Compact: Story = {
    args: { title: "Dividend Yield", value: "1.8%", compact: true, align: "center" },
};