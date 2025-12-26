// src/components/molecules/TickerCard/TickerCard.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs";
import TickerCard from "./TickerCard";

const meta: Meta<typeof TickerCard> = {
    title: "Molecules/TickerCard",
    component: TickerCard,
    args: {
        symbol: "NIKKEI225",
        name: "日経平均",
        price: 39215,
        changePct: 0.85,
        size: "md",
    },
    argTypes: {
        size: { control: "inline-radio", options: ["sm", "md"] },
        changePct: { control: { type: "number", min: -10, max: 10, step: 0.1 } },
        price: { control: { type: "number", min: 0, step: 1 } },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof TickerCard>;

export const Default: Story = {};

export const Negative: Story = {
    args: {
        symbol: "6758.T",
        name: "ソニーG",
        price: 12650,
        changePct: -1.8,
    },
};

export const Small: Story = {
    args: {
        size: "sm",
        symbol: "TOPIX",
        name: "TOPIX",
        price: 2798,
        changePct: 0.12,
    },
};