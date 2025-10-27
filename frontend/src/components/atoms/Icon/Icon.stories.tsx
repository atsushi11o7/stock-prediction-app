// src/components/atoms/Icon/Icon.stories.tsx
import type { Meta, StoryObj } from "@storybook/react";
import Icon, { type IconName } from "./Icon";

const names: IconName[] = ["home", "lineChart", "newspaper", "trendingUp", "compare", "search"];

const meta: Meta<typeof Icon> = {
    title: "Atoms/Icon",
    component: Icon,
    parameters: { layout: "padded" },
    argTypes: {
        name: { control: "select", options: names },
        size: { control: { type: "number", min: 12, max: 64, step: 1 } },
        strokeWidth: { control: { type: "number", min: 1, max: 3, step: 0.25 } },
        className: { control: "text" },
    },
    args: {
        name: "home",
        size: 20,
        strokeWidth: 2,
    },
};
export default meta;

type Story = StoryObj<typeof Icon>;

export const Default: Story = {
    args: {
        className: "aiueo\n"
    }
};

export const Colors: Story = {
    render: () => (
        <div className="flex items-center gap-6">
        <Icon name="home" size={24} className="text-zinc-400" />
        <Icon name="lineChart" size={24} className="text-fuchsia-600" />
        <Icon name="trendingUp" size={24} className="text-emerald-500" />
        <Icon name="newspaper" size={24} className="text-sky-500" />
        </div>
    ),
};

export const Sizes: Story = {
    render: () => (
        <div className="flex items-end gap-6">
        <Icon name="home" size={16} />
        <Icon name="home" size={20} />
        <Icon name="home" size={24} />
        <Icon name="home" size={32} />
        </div>
    ),
};

export const All: Story = {
    args: {
        className: "\n"
    },

    render: () => (
        <div className="grid grid-cols-3 gap-4">
        {names.map((n) => (
            <div key={n} className="flex items-center gap-3 rounded-lg border border-white/10 p-3">
            <Icon name={n} size={20} />
            <span className="text-sm text-zinc-300">{n}</span>
            </div>
        ))}
        </div>
    )
};