import type { Meta, StoryObj } from "@storybook/react";
import NavItem from "./NavItem";

const meta: Meta<typeof NavItem> = {
    title: "Atoms/NavItem",
    component: NavItem,
    args: {
        href: "/stocks",
        label: "Stocks",
        icon: "lineChart",
        variant: "pill",
        size: "md",
    },
    argTypes: {
        variant: { control: "inline-radio", options: ["pill", "glass"] },
        size: { control: "inline-radio", options: ["sm", "md"] },
        href: { control: "text" },
        label: { control: "text" },
        icon: {
        control: "inline-radio",
        options: ["home", "lineChart", "newspaper", "trendingUp", "compare", "search"],
        },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
        nextjs: {
        appDirectory: true,
        navigation: { pathname: "/" },
        },
    },
};
export default meta;

type Story = StoryObj<typeof NavItem>;

export const Default: Story = {};

export const ActiveOnStocks: Story = {
    name: "Active on /stocks",
    parameters: {
        nextjs: { appDirectory: true, navigation: { pathname: "/stocks" } },
    },
};

export const HomeActive: Story = {
    name: "Home item (active on /)",
    args: { href: "/", label: "Home", icon: "home" },
    parameters: {
        nextjs: { appDirectory: true, navigation: { pathname: "/" } },
    },
};

export const GlassInactive: Story = {
    name: "Glass (inactive)",
    args: { variant: "glass", label: "News", icon: "newspaper", href: "/news" },
};

export const SmallSize: Story = {
    name: "Small (sm)",
    args: { size: "sm", label: "Compare", icon: "compare", href: "/compare" },
};