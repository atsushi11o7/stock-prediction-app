// src/components/atoms/StatCard/StatCard.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs";
import { TrendingUp, TrendingDown, Users, DollarSign } from "lucide-react";
import StatCard from "./StatCard";

const meta: Meta<typeof StatCard> = {
    title: "Atoms/StatCard",
    component: StatCard,
    args: {
        label: "Total Stocks",
        value: "31",
        tone: "neutral",
    },
    argTypes: {
        tone: { control: "inline-radio", options: ["success", "danger", "neutral", "brand"] },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof StatCard>;

export const Default: Story = {};

export const WithSubvalue: Story = {
    args: {
        label: "Advancing Stocks",
        value: "18",
        subvalue: "58.1%",
        tone: "success",
    },
};

export const WithIcon: Story = {
    args: {
        label: "Average Change",
        value: "+0.52%",
        tone: "success",
        icon: <TrendingUp size={20} />,
    },
};

export const ToneExamples: Story = {
    render: () => (
        <div className="grid grid-cols-2 gap-4 max-w-2xl">
            <StatCard
                label="Advancing"
                value="18"
                subvalue="58.1%"
                tone="success"
                icon={<TrendingUp size={20} />}
            />
            <StatCard
                label="Declining"
                value="11"
                subvalue="35.5%"
                tone="danger"
                icon={<TrendingDown size={20} />}
            />
            <StatCard
                label="Total Stocks"
                value="31"
                tone="neutral"
                icon={<Users size={20} />}
            />
            <StatCard
                label="Avg Return"
                value="+5.2%"
                tone="brand"
                icon={<DollarSign size={20} />}
            />
        </div>
    ),
};

export const MarketOverview: Story = {
    render: () => (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard label="全銘柄数" value="31" tone="neutral" />
            <StatCard label="値上がり銘柄" value="18" subvalue="58.1%" tone="success" />
            <StatCard label="値下がり銘柄" value="11" subvalue="35.5%" tone="danger" />
            <StatCard label="平均変動率" value="+0.52%" tone="success" />
        </div>
    ),
};
