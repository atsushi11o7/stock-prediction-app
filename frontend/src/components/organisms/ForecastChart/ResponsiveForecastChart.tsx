"use client";

import * as React from "react";
import ForecastChart, { type ForecastChartProps } from "./ForecastChart";
import { useElementSize } from "@/libs/hooks/useElementSize";

/**
 * 親の幅に合わせて ForecastChart の width/height を自動決定する薄いラッパー
 * - aspectRatio: 幅:高さ（例 16/9 = 1.777...）
 * - min/max 高さを設けて“縦に伸びすぎ・潰れすぎ”を防止
 */
export type ResponsiveForecastChartProps = Omit<
    ForecastChartProps,
    "width" | "height"
> & {
    aspectRatio?: number;  // 例: 16/9=1.777..., デフォルト 16/9
    minHeight?: number;    // 最低高さ
    maxHeight?: number;    // 最高高さ
    className?: string;
};

export default function ResponsiveForecastChart({
    aspectRatio = 16 / 9,
    minHeight = 280,
    maxHeight = 520,
    className,
    ...chartProps
}: ResponsiveForecastChartProps) {
    const { ref, size } = useElementSize<HTMLDivElement>();

    // 親幅に追従して高さを計算
    const width = Math.max(0, Math.floor(size.width));
    const idealH = Math.floor(width / aspectRatio);
    const height = Math.max(minHeight, Math.min(maxHeight, idealH));

    return (
        <div ref={ref} className={className} style={{ width: "100%" }}>
            {width > 0 && (
                <ForecastChart
                    {...chartProps}
                    width={width}
                    height={height}
                />
            )}
        </div>
    );
}