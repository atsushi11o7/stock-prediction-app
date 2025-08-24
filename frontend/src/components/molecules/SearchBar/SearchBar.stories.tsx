import type { Meta, StoryObj } from "@storybook/react";
import SearchBar from "./SearchBar";

const meta: Meta<typeof SearchBar> = {
  title: "Molecules/SearchBar",
  component: SearchBar,
  args: { size: "md", placeholder: "Search tickers, companies, news…", actionPath: "/search" },
  parameters: { layout: "padded", backgrounds: { default: "dark" }, nextjs: { appDirectory: true } },
};
export default meta;

type Story = StoryObj<typeof SearchBar>;

export const Default: Story = {};
export const SmallSidebarFit: Story = { args: { size: "sm" } };