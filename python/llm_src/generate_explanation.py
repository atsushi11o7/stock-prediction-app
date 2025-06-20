# python/generate_explanation.py

import openai
import pandas as pd
import os
import json
from datetime import datetime

# OpenAI APIキー設定（環境変数から取得推奨）
openai.api_key = os.getenv("OPENAI_API_KEY")

def load_prediction_data(pred_path: str) -> pd.DataFrame:
    """
    予測結果ファイルを読み込む。

    Args:
        pred_path (str): 予測結果CSVのパス

    Returns:
        pd.DataFrame: 予測結果データフレーム
    """
    return pd.read_csv(pred_path)

def load_recent_data(ticker: str, raw_data_dir: str = "data/raw/") -> pd.DataFrame:
    """
    指定ティッカーの過去データを読み込む

    Args:
        ticker (str): ティッカーシンボル
        raw_data_dir (str): データディレクトリ

    Returns:
        pd.DataFrame: 株価データフレーム（直近30日間）
    """
    path = os.path.join(raw_data_dir, f"{ticker}_merged.csv")
    df = pd.read_csv(path, parse_dates=['Date'])
    return df.tail(30)

def build_prompt(ticker: str, history_df: pd.DataFrame, pred_row: pd.Series, news_data: dict) -> str:
    """
    LLM用プロンプトを作成する。

    Args:
        ticker (str): ティッカーシンボル
        history_df (pd.DataFrame): 過去30日間データ
        pred_row (pd.Series): 未来7日間予測データ
        news_data (dict): ニュース感情データと要約（存在しない場合は空）

    Returns:
        str: プロンプトテキスト
    """
    past_price_info = "\n".join([
        f"{row['Date'].strftime('%Y-%m-%d')}: Close={row['Close']:.2f}, MA_5={row.get('MA_5',0):.2f}, RSI={row.get('RSI',0):.2f}, MACD={row.get('MACD',0):.2f}" 
        for _, row in history_df.tail(5).iterrows()
    ])

    news_info = "\n".join([
        f"{d['date']}: 感情スコア={d['score']:.2f}, ニュース={d['summary']}"
        for d in news_data.get(ticker, [])
    ])

    future_pred = ", ".join([f"Day{i+1}: {pred_row[f'Day{i+1}']:.2f}" for i in range(7)])

    prompt = f"""
    あなたは株式市場の専門アナリストです。
    以下の情報を参考に、今後7営業日の株価推移に関する見解を、ビジネス文体で200〜400文字程度で説明してください。

    【過去5営業日の株価データ】
    {past_price_info}

    【最近のニュース感情情報】
    {news_info if news_info else '直近に特筆すべきニュースはありません。'}

    【今後7営業日の株価予測】
    {future_pred}

    注意：事実に基づきながらも、あくまで推測であることを前提に柔らかい表現でまとめてください。
    """
    return prompt

def query_openai(prompt: str) -> str:
    """
    OpenAI APIを使って回答を得る

    Args:
        prompt (str): 入力プロンプト

    Returns:
        str: LLMの出力テキスト
    """
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "あなたはプロの金融アナリストです。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response['choices'][0]['message']['content']

def main():
    pred_df = load_prediction_data("predictions/predictions.csv")

    # ニュースデータ仮（本来はデータベースや別ファイルからロードする）
    try:
        with open("data/news_summary.json", "r") as f:
            news_data = json.load(f)
    except FileNotFoundError:
        news_data = {}

    explanations = []

    for _, row in pred_df.iterrows():
        ticker = row['Ticker']
        history_df = load_recent_data(ticker)
        prompt = build_prompt(ticker, history_df, row, news_data)
        explanation = query_openai(prompt)
        explanations.append({"Ticker": ticker, "Explanation": explanation})

    output_df = pd.DataFrame(explanations)
    os.makedirs("predictions/", exist_ok=True)
    output_df.to_csv("predictions/explanations.csv", index=False)

if __name__ == "__main__":
    main()
