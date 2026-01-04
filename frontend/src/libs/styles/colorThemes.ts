/**
 * カラーテーマ定義
 * 複数のコンポーネントで使用される色・トーンのマッピングを集約
 */

/**
 * テキストカラーのトーン
 */
export const textColorMap = {
    success: "text-[var(--color-success)]",
    danger: "text-[var(--color-danger)]",
    neutral: "text-[var(--color-text-1)]",
    brand: "text-[var(--color-brand-500)]",
    muted: "text-[var(--color-text-2)]",
} as const;

export type TextColorTone = keyof typeof textColorMap;

/**
 * 背景カラーのトーン (Badge等で使用)
 */
export const bgColorMap = {
    brand: "bg-[var(--color-brand-600)] text-white",
    success: "bg-[var(--color-success)] text-white",
    danger: "bg-[var(--color-danger)] text-white",
    muted: "bg-[var(--color-surface-2)] text-[var(--color-text-2)]",
} as const;

export type BgColorTone = keyof typeof bgColorMap;

/**
 * MetricTileやチャート等で使用される方向性トーン
 */
export const directionColorMap = {
    neutral: "text-[var(--color-text-1)]",
    up: "text-[var(--color-success)]",
    down: "text-[var(--color-danger)]",
    brand: "text-[var(--color-brand-600)]",
} as const;

export type DirectionColorTone = keyof typeof directionColorMap;
