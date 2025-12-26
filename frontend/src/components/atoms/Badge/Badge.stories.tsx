// src/components/atoms/Badge/Badge.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs"
import Badge from "./Badge";

const meta: Meta<typeof Badge> = {
    title: "Atoms/Badge",
    component: Badge,
    args: {
        children: "NEW",
        tone: "brand",
        size: "md",
        rounded: "full",
    },
    argTypes: {
        tone: { control: "inline-radio", options: ["brand", "success", "danger", "muted"] },
        size: { control: "inline-radio", options: ["sm", "md"] },
        rounded: { control: "inline-radio", options: ["sm", "md", "full"] },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof Badge>;

export const Default: Story = {};

export const StatusExamples: Story = {
    render: () => (
        <div className="space-x-2">
            <Badge tone="brand">Brand</Badge>
            <Badge tone="success">Up</Badge>
            <Badge tone="danger">Down</Badge>
            <Badge tone="muted">Muted</Badge>
        </div>
    ),
};