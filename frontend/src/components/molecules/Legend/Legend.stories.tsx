import type { Meta, StoryObj } from "@storybook/nextjs";
import Legend from "./Legend";

const meta = {
    title: "Molecules/Legend",
    component: Legend,
    args: {
        items: [
            { color: "var(--color-brand-600)", label: "Actual" },
            { color: "#6DDB5E", label: "Forecast" },
            { color: "rgba(109,219,94,0.45)", label: "Forecast (past)" },
        ],
        direction: "row",
        wrap: true,
        density: "md",
        align: "start",
    },
    argTypes: {
        direction: { control: "inline-radio", options: ["row", "column"] },
        wrap: { control: "boolean" },
        density: { control: "inline-radio", options: ["sm", "md"] },
        align: { control: "inline-radio", options: ["start", "center", "end", "between"] },
    },
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
} satisfies Meta<typeof Legend>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const CenteredTight: Story = {
    name: "Centered / tight gap",
    args: {
        density: "sm",
        align: "center",
    },
};

export const Column: Story = {
    name: "Column layout",
    args: {
        direction: "column",
        wrap: false,
    },
};

export const ManyItemsWrap: Story = {
    name: "Many items (wrap)",
    args: {
        items: [
            { color: "var(--color-brand-600)", label: "Actual" },
            { color: "#6DDB5E", label: "Forecast" },
            { color: "rgba(109,219,94,0.45)", label: "Forecast (past)" },
            { color: "#F59E0B", label: "SMA 50" },
            { color: "#60A5FA", label: "SMA 200" },
            { color: "#F43F5E", label: "Drawdown" },
        ],
        wrap: true,
        align: "start",
    },
};