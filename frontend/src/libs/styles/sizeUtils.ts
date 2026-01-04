/**
 * サイズ関連のスタイルマッピング
 * 複数のコンポーネントで使用されるサイズに基づくスタイルを集約
 */

/**
 * 共通サイズ型
 */
export type Size = "sm" | "md" | "lg";

/**
 * パディングのサイズマップ
 */
export const paddingSizeMap = {
    sm: "px-3 py-2",
    md: "px-4 py-3",
    lg: "px-5 py-4",
} as const;

/**
 * テキストサイズマップ
 */
export const textSizeMap = {
    xs: "text-[11px]",
    sm: "text-[13px]",
    md: "text-sm",
    lg: "text-base",
    xl: "text-lg",
} as const;

/**
 * カードパディングマップ
 */
export const cardPaddingSizeMap = {
    sm: "p-3",
    md: "p-4",
    lg: "p-5",
} as const;

/**
 * アイコンサイズマップ (ピクセル値)
 */
export const iconSizeMap = {
    sm: 18,
    md: 20,
    lg: 24,
} as const;

/**
 * ギャップサイズマップ
 */
export const gapSizeMap = {
    sm: "gap-3.5",
    md: "gap-4",
    lg: "gap-5",
} as const;
