"use client";

export default function RailCard({
    title,
    children,
}: {
    title: string;
    children?: React.ReactNode;
}) {
    return (
        <section className="rounded-2xl border border-white/10 bg-[var(--color-surface-1)] p-4">
            <h3 className="mb-3 text-sm font-semibold text-[var(--color-text-2)]">{title}</h3>
            {children}
        </section>
    );
}