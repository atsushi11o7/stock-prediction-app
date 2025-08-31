import type { Meta, StoryObj } from "@storybook/react";
import Label from "./Label";

const meta: Meta<typeof Label> = {
    title: "Atoms/Label",
    component: Label,
    args: {
        children: "Key Metrics",
        size: "sm",
        tone: "secondary",
        weight: "medium",
        align: "left",
        leading: "normal",
        uppercase: false,
        truncate: false,
    },
    argTypes: {
        size: { control: "inline-radio", options: ["xs", "sm", "md", "lg"] },
        tone: { control: "inline-radio", options: ["primary", "secondary", "muted", "brand", "success", "danger"] },
        weight: { control: "inline-radio", options: ["normal", "medium", "semibold", "bold"] },
        align: { control: "inline-radio", options: ["left", "center", "right"] },
        leading: { control: "inline-radio", options: ["tight", "snug", "normal"] },
        uppercase: { control: "boolean" },
        truncate: { control: "boolean" },
        as: { control: "inline-radio", options: ["span", "p", "div"] },
        className: { control: false },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof Label>;

export const Default: Story = {};

export const Headline: Story = {
    name: "Headline / primary + bold",
    args: { children: "Key Metrics", size: "lg", tone: "primary", weight: "bold" },
};

export const MutedNote: Story = {
    name: "Muted note",
    args: { children: "PER = Price / EPS", size: "xs", tone: "muted" },
};

export const StatusColors: Story = {
    name: "Status colors",
    render: () => (
        <div className="space-y-2">
            <Label tone="brand" weight="semibold">Brand color</Label>
            <Label tone="success" weight="semibold">+2.1% Up</Label>
            <Label tone="danger" weight="semibold">-1.2% Down</Label>
        </div>
    ),
};

export const TruncateExample: Story = {
    name: "Truncate (ellipsis)",
    render: () => (
        <div className="w-[220px]">
            <Label truncate>
                Very long stock headline that will be truncated with an ellipsis if it overflows
            </Label>
        </div>
    ),
};