// ドメイン ↔ レンジの一次変換スケール & ユーティリティ

export function createLinear(
    domain: [number, number],
    range: [number, number]
) {
    const [d0, d1] = domain;
    const [r0, r1] = range;
    const m = (r1 - r0) / (d1 - d0 || 1);
    return (v: number) => r0 + (v - d0) * m;
}

/** 値配列から最小・最大を返す（null/NaN を除外） */
export function extent(values: Array<number | null | undefined>): [number, number] {
    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;
    for (const v of values) {
        if (v == null || !Number.isFinite(v)) continue;
        if (v < min) min = v;
        if (v > max) max = v;
    }
    if (min === Number.POSITIVE_INFINITY || max === Number.NEGATIVE_INFINITY) {
        return [0, 1];
    }
    return [min, max];
}

/** 複数 Series から min/max を求める */
export function extentFromSeries(seriesList: Array<Array<number | null>>): [number, number] {
    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;
    for (const s of seriesList) {
        for (const v of s) {
            if (v == null || !Number.isFinite(v)) continue;
            if (v < min) min = v;
            if (v > max) max = v;
        }
    }
    if (min === Number.POSITIVE_INFINITY || max === Number.NEGATIVE_INFINITY) {
        return [0, 1];
    }
    return [min, max];
}

/** 見栄えよく丸めたドメインを返す（ticksCount 目安） */
export function niceDomain([min, max]: [number, number], ticksCount = 4): [number, number] {
    if (min === max) {
        // 全て同値のときは±1幅で表示
        return [min - 1, max + 1];
    }
    const span = max - min;
    const step = niceStep(span / Math.max(1, ticksCount));
    const niceMin = Math.floor(min / step) * step;
    const niceMax = Math.ceil(max / step) * step;
    return [niceMin, niceMax];
}

function niceStep(rawStep: number) {
    const pow10 = Math.pow(10, Math.floor(Math.log10(Math.abs(rawStep))));
    const err = rawStep / pow10;
    const nice =
        err >= 7.5 ? 10 :
        err >= 3.5 ? 5 :
        err >= 1.5 ? 2 : 1;
    return nice * pow10;
}