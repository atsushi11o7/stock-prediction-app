import type { Meta, StoryObj } from "@storybook/react";
import Logo from "./Logo";

const meta: Meta<typeof Logo> = {
    title: "Atoms/Logo",
    component: Logo,
    args: { width: 200 },
    argTypes: {
        width: { control: { type: "number", min: 80, max: 600, step: 5 } },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof Logo>;

export const Default: Story = {};

export const Narrow: Story = {
    args: { width: 140 },
};

export const Wide: Story = {
    args: { width: 320 },
};