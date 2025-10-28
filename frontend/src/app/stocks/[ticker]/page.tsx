import { notFound } from "next/navigation";

type PageProps = {
    params: { ticker: string };               // 動的セグメント
    searchParams?: Record<string, string>;
};

export const revalidate = 300;                // ← 任意（ISR 5分など）

export default async function StockPage({ params }: PageProps) {
    const { ticker } = params;

    if (!ticker) {
        notFound();
    }

    // ここでデータ取得（サーバーコンポーネント内でOK）
    // const data = await getForecast(ticker).catch(() => null);

    return (
        <main className="p-6">
            <h1 className="text-2xl font-bold">{ticker} detail</h1>
            {/* 取得データで詳細を描画 */}
        </main>
    );
}