import type { Meta, StoryObj } from "@storybook/react";
import SectorPerformance from "./SectorPerformance";
import type { StockDetail } from "@/libs/repositories/stockRepository";

const mockStocks: StockDetail[] = [
    // Technology
    {
        ticker: "6857.T",
        code: "6857",
        name: "アドバンテスト",
        sector: "Technology",
        industry: "Semiconductor Equipment",
        price: 19635,
        changePct: -0.73,
        kpi: { per: 35.2, pbr: 8.5, dividendYield: 0.5 },
        forecast: { predicted12mReturn: 157.32 },
    },
    {
        ticker: "8035.T",
        code: "8035",
        name: "東京エレクトロン",
        sector: "Technology",
        industry: "Semiconductor Equipment",
        price: 34320,
        changePct: 0.26,
        kpi: { per: 28.5, pbr: 6.2, dividendYield: 1.2 },
        forecast: { predicted12mReturn: 69.12 },
    },
    {
        ticker: "6758.T",
        code: "6758",
        name: "ソニーグループ",
        sector: "Technology",
        industry: "Consumer Electronics",
        price: 4024,
        changePct: -0.12,
        kpi: { per: 19.96, pbr: 3.11, dividendYield: 0.63 },
        forecast: { predicted12mReturn: 41.06 },
    },
    // Industrials
    {
        ticker: "8031.T",
        code: "8031",
        name: "三井物産",
        sector: "Industrials",
        industry: "Trading Companies",
        price: 4643,
        changePct: -1.0,
        kpi: { per: 8.5, pbr: 1.3, dividendYield: 3.5 },
        forecast: { predicted12mReturn: 48.03 },
    },
    {
        ticker: "8058.T",
        code: "8058",
        name: "三菱商事",
        sector: "Industrials",
        industry: "Trading Companies",
        price: 3586,
        changePct: 0.48,
        kpi: { per: 12.3, pbr: 1.5, dividendYield: 3.2 },
        forecast: { predicted12mReturn: 45.62 },
    },
    {
        ticker: "6367.T",
        code: "6367",
        name: "ダイキン工業",
        sector: "Industrials",
        industry: "Building Products",
        price: 20080,
        changePct: 0.96,
        kpi: { per: 25.3, pbr: 4.2, dividendYield: 1.0 },
        forecast: { predicted12mReturn: 41.12 },
    },
    // Healthcare
    {
        ticker: "4502.T",
        code: "4502",
        name: "武田薬品工業",
        sector: "Healthcare",
        industry: "Pharmaceuticals",
        price: 4835,
        changePct: -1.45,
        kpi: { per: 25.8, pbr: 1.1, dividendYield: 4.5 },
        forecast: { predicted12mReturn: -84.9 },
    },
    // Consumer Defensive
    {
        ticker: "2914.T",
        code: "2914",
        name: "日本たばこ産業",
        sector: "Consumer Defensive",
        industry: "Tobacco",
        price: 5640,
        changePct: -0.48,
        kpi: { per: 15.2, pbr: 2.1, dividendYield: 4.8 },
        forecast: { predicted12mReturn: -12.97 },
    },
    {
        ticker: "3382.T",
        code: "3382",
        name: "セブン&アイ・ホールディングス",
        sector: "Consumer Defensive",
        industry: "Retail",
        price: 2250,
        changePct: -0.97,
        kpi: { per: 18.5, pbr: 1.8, dividendYield: 2.5 },
        forecast: { predicted12mReturn: -3.36 },
    },
    // Financial Services
    {
        ticker: "8766.T",
        code: "8766",
        name: "東京海上ホールディングス",
        sector: "Financial Services",
        industry: "Insurance",
        price: 5817,
        changePct: -0.33,
        kpi: { per: 12.5, pbr: 1.6, dividendYield: 3.0 },
        forecast: { predicted12mReturn: 22.44 },
    },
];

const meta: Meta<typeof SectorPerformance> = {
    title: "Organisms/SectorPerformance",
    component: SectorPerformance,
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
    decorators: [
        (Story) => (
            <div style={{ maxWidth: 800, margin: "0 auto" }}>
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof SectorPerformance>;

export const Default: Story = {
    args: {
        stocks: mockStocks,
    },
};

export const EmptyState: Story = {
    args: {
        stocks: [],
    },
};
