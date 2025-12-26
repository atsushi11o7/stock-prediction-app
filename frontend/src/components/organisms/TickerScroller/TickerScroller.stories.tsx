import type { Meta, StoryObj } from "@storybook/nextjs";
import TickerScroller from "./TickerScroller";

const meta: Meta<typeof TickerScroller> = {
    title: "Organisms/TickerScroller",
    component: TickerScroller,
    args: {
        indices: [
            { symbol: "NIKKEI225", name: "日経平均", price: 39215, changePct: 0.85 },
            { symbol: "TOPIX", name: "TOPIX", price: 2798, changePct: -0.12 },
        ],
        movers: [
            { symbol: "7203.T", name: "トヨタ", price: 2431, changePct: 2.1 },
            { symbol: "6758.T", name: "ソニーG", price: 12650, changePct: -1.8 },
            { symbol: "9984.T", name: "ソフトバンクG", price: 8210, changePct: 3.4 },
            { symbol: "8035.T", name: "東京エレクトロン", price: 38150, changePct: 4.9 },
            { symbol: "6954.T", name: "ファナック", price: 4590, changePct: -0.6 },
            { symbol: "9433.T", name: "KDDI", price: 4440, changePct: 0.3 },
            { symbol: "9432.T", name: "NTT", price: 176, changePct: -2.5 },
            { symbol: "7974.T", name: "任天堂", price: 8030, changePct: 1.2 },
            { symbol: "4063.T", name: "信越化学", price: 6190, changePct: 0.9 },
            { symbol: "6098.T", name: "リクルート", price: 6170, changePct: -0.7 },
        ],
        seeAll: { href: "/stocks", label: "株価一覧へ" },
    },
    parameters: {
        layout: "fullscreen",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof TickerScroller>;

export const Default: Story = {
    render: (args) => (
        <div className="p-6">
            {/* 横幅が狭い環境でも動きが分かるように、中央に最大幅を用意 */}
            <div className="mx-auto max-w-5xl">
                <TickerScroller {...args} />
            </div>
        </div>
    ),
};

export const ManyItems: Story = {
    args: {
        movers: Array.from({ length: 18 }).map((_, i) => ({
            symbol: `MOCK${i + 1}.T`,
            name: `モック銘柄${i + 1}`,
            price: 1000 + i * 123,
            changePct: (i % 2 === 0 ? 1 : -1) * (0.3 + (i % 5) * 0.4),
        })),
    },
};