import type { Meta, StoryObj } from "@storybook/nextjs";
import TrendsRanking from "./TrendsRanking";
import type { StockDetail } from "@/libs/repositories/stockRepository";

const mockStocks: StockDetail[] = [
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
];

const meta: Meta<typeof TrendsRanking> = {
    title: "Organisms/TrendsRanking",
    component: TrendsRanking,
    parameters: {
        layout: "padded",
        backgrounds: { default: "dark" },
    },
    decorators: [
        (Story) => (
            <div style={{ maxWidth: 600, margin: "0 auto" }}>
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof TrendsRanking>;

export const Top10: Story = {
    args: {
        stocks: mockStocks,
        title: "予測リターン TOP10",
        type: "top",
        limit: 10,
    },
};

export const Worst10: Story = {
    args: {
        stocks: mockStocks,
        title: "予測リターン WORST10",
        type: "bottom",
        limit: 10,
    },
};

export const Top5: Story = {
    args: {
        stocks: mockStocks,
        title: "予測リターン TOP5",
        type: "top",
        limit: 5,
    },
};

export const EmptyState: Story = {
    args: {
        stocks: [],
        title: "予測リターン TOP10",
        type: "top",
        limit: 10,
    },
};
