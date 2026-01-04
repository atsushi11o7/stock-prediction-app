/**
 * 共通のフォーマット関数
 * 複数のコンポーネントで使用される数値・通貨フォーマット処理を集約
 */

/**
 * 日本円フォーマット
 * @param value - フォーマットする数値
 * @param prefix - 接頭辞 ("¥" または "円")
 * @returns フォーマットされた文字列
 */
export function formatYen(value: number | undefined | null, prefix: "¥" | "円" = "¥"): string {
    if (value === undefined || value === null || isNaN(value)) {
        return "N/A";
    }
    const formatted = value.toLocaleString("ja-JP");
    return prefix === "¥" ? `¥${formatted}` : `${formatted}円`;
}

/**
 * パーセンテージフォーマット
 * @param value - フォーマットする数値
 * @param decimals - 小数点以下の桁数 (デフォルト: 2)
 * @returns フォーマットされた文字列 (例: "+2.50%", "-1.23%")
 */
export function formatPercent(value: number | undefined | null, decimals: number = 2): string {
    if (value === undefined || value === null || isNaN(value)) {
        return "N/A";
    }
    const sign = value > 0 ? "+" : "";
    return `${sign}${value.toFixed(decimals)}%`;
}

/**
 * 数値を3桁区切りでフォーマット
 * @param value - フォーマットする数値
 * @returns フォーマットされた文字列
 */
export function formatNumber(value: number | undefined | null): string {
    if (value === undefined || value === null || isNaN(value)) {
        return "N/A";
    }
    return value.toLocaleString("ja-JP");
}
