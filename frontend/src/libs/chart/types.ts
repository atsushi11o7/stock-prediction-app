// 共有型

export type Series = (number | null)[];

export type HistoricalPrediction = {
    /** その予測が作られた時点（インデックス） */
    asOfIndex: number;
    /** 全期間の値（未来側は描画側でクリップ） */
    values: Series;
};

export type StockForecastData = {
    /** ティッカー（必須。画面にも表示） */
    ticker: string;

    /** x 軸ラベル（例: "YYYY-MM"） */
    labels: string[];

    /** 実績（predictStartIndex 以降は null 想定） */
    actual: Series;

    /** 未来予測（predictStartIndex 以前は null 想定） */
    predicted: Series;

    /** 過去予測のバージョン群（複数）。描画時に “今まで”へクリップして使う */
    historicalPredictions: HistoricalPrediction[];

    /** 予測開始のインデックス（ここを境に実績→未来） */
    predictStartIndex: number;

    /** モデル注釈（任意） */
    comment?: string;
};