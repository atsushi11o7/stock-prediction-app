import type { Meta, StoryObj } from "@storybook/react";
import LineChip from "./LineChip";

const meta = {
    title: "Atoms/LineChip",
    component: LineChip,
    args: {
        color: "var(--color-brand-600)",
        label: "Forecast",
    },
    argTypes: {
        color: { control: "color" },
        label: { control: "text" },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
} satisfies Meta<typeof LineChip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Variants: Story = {
    render: () => (
        <div className="space-y-2">
            <LineChip color="var(--color-brand-600)" label="Forecast" />
            <LineChip color="var(--color-success)" label="Actual" />
            <LineChip color="var(--color-danger)" label="Error" />
        </div>
    ),
};