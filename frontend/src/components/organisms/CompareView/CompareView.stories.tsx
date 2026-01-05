import type { Meta, StoryObj } from "@storybook/react";
import CompareView from "./CompareView";
import type { StockDetail } from "@/libs/repositories/stockRepository";

const mockStocks: StockDetail[] = [
    {
        ticker: "7203.T",
        code: "7203",
        name: "トヨタ自動車",
        sector: "Consumer Cyclical",
        industry: "Auto Manufacturers",
        price: 2850,
        changePct: 1.25,
        kpi: { per: 10.5, pbr: 1.2, dividendYield: 2.8, roe: 12.5 },
        forecast: { predicted12mReturn: 15.5 },
    },
    {
        ticker: "6758.T",
        code: "6758",
        name: "ソニーグループ",
        sector: "Technology",
        industry: "Consumer Electronics",
        price: 4024,
        changePct: -0.12,
        kpi: { per: 19.96, pbr: 3.11, dividendYield: 0.63, roe: 15.8 },
        forecast: { predicted12mReturn: 41.06 },
    },
    {
        ticker: "6857.T",
        code: "6857",
        name: "アドバンテスト",
        sector: "Technology",
        industry: "Semiconductor Equipment",
        price: 19635,
        changePct: -0.73,
        kpi: { per: 35.2, pbr: 8.5, dividendYield: 0.5, roe: 25.3 },
        forecast: { predicted12mReturn: 157.32 },
    },
    {
        ticker: "8058.T",
        code: "8058",
        name: "三菱商事",
        sector: "Industrials",
        industry: "Trading Companies",
        price: 3586,
        changePct: 0.48,
        kpi: { per: 12.3, pbr: 1.5, dividendYield: 3.2, roe: 14.2 },
        forecast: { predicted12mReturn: 45.62 },
    },
    {
        ticker: "4502.T",
        code: "4502",
        name: "武田薬品工業",
        sector: "Healthcare",
        industry: "Pharmaceuticals",
        price: 4835,
        changePct: -1.45,
        kpi: { per: 25.8, pbr: 1.1, dividendYield: 4.5, roe: 5.2 },
        forecast: { predicted12mReturn: -84.9 },
    },
    {
        ticker: "9983.T",
        code: "9983",
        name: "ファーストリテイリング",
        sector: "Consumer Cyclical",
        industry: "Apparel Retail",
        price: 56940,
        changePct: 0.98,
        kpi: { per: 42.5, pbr: 8.2, dividendYield: 0.8, roe: 22.5 },
        forecast: { predicted12mReturn: -0.17 },
    },
];

const meta: Meta<typeof CompareView> = {
    title: "Organisms/CompareView",
    component: CompareView,
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
        nextjs: {
            appDirectory: true,
            navigation: {
                pathname: "/compare",
            },
        },
    },
    decorators: [
        (Story) => (
            <div style={{ maxWidth: 1000, margin: "0 auto" }}>
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof CompareView>;

export const Empty: Story = {
    args: {
        stocks: mockStocks,
        initialTickers: [],
    },
};

export const TwoStocks: Story = {
    args: {
        stocks: mockStocks,
        initialTickers: ["7203.T", "6758.T"],
    },
};

export const ThreeStocks: Story = {
    args: {
        stocks: mockStocks,
        initialTickers: ["7203.T", "6758.T", "8058.T"],
    },
};

export const FourStocks: Story = {
    args: {
        stocks: mockStocks,
        initialTickers: ["7203.T", "6758.T", "8058.T", "6857.T"],
    },
};

export const MixedPerformance: Story = {
    args: {
        stocks: mockStocks,
        initialTickers: ["6857.T", "4502.T"],
    },
};
