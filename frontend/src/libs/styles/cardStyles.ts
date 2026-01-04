/**
 * カードコンポーネント共通スタイル
 * StatCard, RailCard, MetricTile等で使用される基本スタイルを集約
 */

/**
 * ベースカードスタイル
 */
export const baseCardClass = [
    "relative overflow-hidden",
    "rounded-2xl",
    "border border-white/10",
    "bg-[var(--color-surface-1)]",
].join(" ");

/**
 * カードホバーエフェクト (軽度)
 */
export const cardHoverLightClass = [
    "transition-all duration-300",
    "hover:border-[var(--color-brand-500)]/20",
    "hover:shadow-lg hover:shadow-[var(--color-brand-500)]/5",
].join(" ");

/**
 * カードホバーエフェクト (中程度)
 */
export const cardHoverMediumClass = [
    "transition-all duration-300",
    "hover:border-[var(--color-brand-500)]/30",
    "hover:shadow-lg hover:shadow-[var(--color-brand-500)]/10",
    "hover:-translate-y-0.5",
].join(" ");

/**
 * カードホバーエフェクト (強度)
 */
export const cardHoverStrongClass = [
    "transition-all duration-300",
    "hover:border-[var(--color-brand-500)]",
    "hover:shadow-xl hover:shadow-[var(--color-brand-500)]/10",
    "hover:-translate-y-1",
].join(" ");

/**
 * カード内オーバーレイ (ホバー時に明るくなる)
 */
export const cardOverlayClass = [
    "absolute inset-0",
    "bg-white/0 group-hover:bg-white/5",
    "transition-opacity duration-300",
].join(" ");
