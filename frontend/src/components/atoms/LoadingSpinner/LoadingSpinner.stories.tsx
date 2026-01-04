// src/components/atoms/LoadingSpinner/LoadingSpinner.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs";
import LoadingSpinner from "./LoadingSpinner";

const meta: Meta<typeof LoadingSpinner> = {
    title: "Atoms/LoadingSpinner",
    component: LoadingSpinner,
    args: {
        size: "md",
    },
    argTypes: {
        size: { control: "inline-radio", options: ["sm", "md", "lg"] },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof LoadingSpinner>;

export const Default: Story = {};

export const WithMessage: Story = {
    args: {
        message: "読み込み中...",
    },
};

export const Sizes: Story = {
    render: () => (
        <div className="flex items-center gap-8">
            <div className="text-center">
                <LoadingSpinner size="sm" />
                <p className="mt-2 text-xs text-[var(--color-text-3)]">Small</p>
            </div>
            <div className="text-center">
                <LoadingSpinner size="md" />
                <p className="mt-2 text-xs text-[var(--color-text-3)]">Medium</p>
            </div>
            <div className="text-center">
                <LoadingSpinner size="lg" />
                <p className="mt-2 text-xs text-[var(--color-text-3)]">Large</p>
            </div>
        </div>
    ),
};

export const InCard: Story = {
    render: () => (
        <div className="rounded-2xl border border-white/10 bg-[var(--color-panel)] p-8">
            <LoadingSpinner message="データを取得中..." />
        </div>
    ),
};
