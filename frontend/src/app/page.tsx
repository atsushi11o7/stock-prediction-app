import Image from "next/image";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-5xl p-6">
      <h1 className="text-2xl font-bold">ようこそ FumiKabu へ</h1>
      <p className="mt-2 text-zinc-400">株価予測やニュースをまとめてチェックできます。</p>

      <div className="mt-6 flex gap-3">
        <a href="/stocks" className="rounded-xl bg-fuchsia-600 px-4 py-3 text-white">銘柄一覧へ</a>
        <a href="/news" className="rounded-xl border border-white/10 px-4 py-3">ニュースへ</a>
      </div>

      {/* ここにユニークなヒーロー、説明、カード、などを配置 */}
    </main>
  );
}
