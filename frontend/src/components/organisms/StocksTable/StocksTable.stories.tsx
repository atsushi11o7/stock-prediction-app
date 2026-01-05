import type { Meta, StoryObj } from "@storybook/nextjs";
import StocksTable from "./StocksTable";
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
];

const meta: Meta<typeof StocksTable> = {
    title: "Organisms/StocksTable",
    component: StocksTable,
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
    decorators: [
        (Story) => (
            <div style={{ maxWidth: 1200, margin: "0 auto" }}>
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof StocksTable>;

export const Default: Story = {
    args: {
        stocks: mockStocks,
    },
};

export const WithInitialSearch: Story = {
    args: {
        stocks: mockStocks,
        initialSearchTerm: "ソニー",
    },
};

export const EmptyState: Story = {
    args: {
        stocks: [],
    },
};

export const SingleStock: Story = {
    args: {
        stocks: [mockStocks[0]],
    },
};
