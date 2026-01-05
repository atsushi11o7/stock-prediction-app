import type { Meta, StoryObj } from "@storybook/nextjs";
import RightRail from "./RightRail";
import RailCard from "@/components/molecules/RailCard";

const meta: Meta<typeof RightRail> = {
    title: "Organisms/RightRail",
    component: RightRail,
    args: {
        paddingClass: "px-4 py-5",
    },
    parameters: {
        layout: "fullscreen",
        backgrounds: { default: "dark" },
    },
};
export default meta;

type Story = StoryObj<typeof RightRail>;

export const Default: Story = {
    render: (args) => (
        <div className="grid grid-cols-[auto_1fr_auto] min-h-dvh">
            {/* 左にサンプルの余白だけ置く（実際は Sidebar が入る想定） */}
            <div className="w-[268px] border-r border-white/10 bg-[var(--color-panel)]" />

            {/* 中央メインのダミー領域 */}
            <main className="px-6 py-6 text-[var(--color-text-3)]">
                <div className="h-[240px] rounded-2xl border border-white/10 bg-[var(--color-panel)] p-4">
                    Main Content (mock)
                </div>
            </main>

            {/* 右レール：children で複数カードを差し込む */}
            <RightRail {...args}>
                <RailCard title="Market Overview">
                    <ul className="space-y-2 text-sm">
                        <li className="flex justify-between"><span>Nikkei 225</span><span className="text-green-400">+0.8%</span></li>
                        <li className="flex justify-between"><span>S&P 500</span><span className="text-red-400">-0.3%</span></li>
                    </ul>
                </RailCard>

                <RailCard title="Top Movers">
                    <ul className="space-y-2 text-sm">
                        <li className="flex justify-between"><span>NVDA</span><span className="text-green-400">+2.1%</span></li>
                        <li className="flex justify-between"><span>TSLA</span><span className="text-red-400">-1.2%</span></li>
                    </ul>
                </RailCard>

                <RailCard title="News Digest">
                    <ul className="space-y-2 text-sm">
                        <li className="hover:underline cursor-pointer">BOJ hints at policy shift</li>
                        <li className="hover:underline cursor-pointer">NVIDIA reaches new high</li>
                    </ul>
                </RailCard>

                <RailCard title="Quick Tip">
                    <p className="text-[var(--color-text-3)] text-sm">
                        PER = 株価 ÷ 1株あたり利益（EPS）
                    </p>
                </RailCard>
            </RightRail>
        </div>
    ),
};