import type { Meta, StoryObj } from "@storybook/nextjs";
import SeeAllCard from "./SeeAllCard";

const meta: Meta<typeof SeeAllCard> = {
    title: "Molecules/SeeAllCard",
    component: SeeAllCard,
    args: {
        href: "/stocks",
        label: "株価一覧へ",
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof SeeAllCard>;

export const Default: Story = {};

export const CustomLabel: Story = {
    args: { label: "もっと見る" },
};