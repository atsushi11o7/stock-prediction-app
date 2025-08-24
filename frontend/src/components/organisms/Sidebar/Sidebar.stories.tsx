import type { Meta, StoryObj } from "@storybook/react";
import Sidebar from "./Sidebar";

const meta: Meta<typeof Sidebar> = {
    title: "Organisms/Sidebar",
    component: Sidebar,
    args: {
        width: 268,
        contentWidth: 220,  // ロゴ / 検索 / NavItem をこの幅で統一
    },
    parameters: {
        layout: "fullscreen",
        backgrounds: { default: "dark" },
        nextjs: {
            appDirectory: true,
            navigation: { pathname: "/" },
            router: {
                push: async (url: string) => console.log("[SB router.push]", url),
                replace: async (url: string) => console.log("[SB router.replace]", url),
                prefetch: async () => {},
                back: () => console.log("[SB router.back]"),
            },
        },
    },
};
export default meta;

type Story = StoryObj<typeof Sidebar>;

export const Default: Story = {};

export const Narrow: Story = {
    name: "Narrow (width=240 / content=200)",
    args: { width: 240, contentWidth: 200 },
};

export const CustomItems: Story = {
    args: {
        width: 268,
        contentWidth: 220,
        items: [
            { href: "/", label: "Home", icon: "home" },
            { href: "/stocks", label: "Stocks", icon: "lineChart" },
            { href: "/news", label: "News", icon: "newspaper" },
            { href: "/trends", label: "Trends", icon: "trendingUp" },
            { href: "/compare", label: "Compare", icon: "compare" },
            { href: "/search", label: "Search", icon: "search" },
        ],
        footerSlot: <span>© FumiKabu</span>,
    },
};