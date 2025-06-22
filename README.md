# stock-prediction-app

MLOps学習用

## 株価予測＆ニュース解説アプリ

企業の株価予測と、ニュース情報を基にした市場動向の解説を行うシステムを作成する。MLOps の手法を取り入れ、継続的なモデルの再学習とファインチューニングを実現するとともに、LLM を活用して「なぜ株がこのような動きをするのか」を解説できることを目指す。

---

## 1. アプリ全体構成の構想

- **フロントエンド**
  - **機能:** ユーザが企業を指定し、株価予測結果やニュースに基づく解説を表示するダッシュボード
  - **使用言語:** TypeScript
  - **主なライブラリ/フレームワーク:**
    - React / Next.js
    - UI コンポーネントライブラリ

- **バックエンド API サービス**
  - **機能:** ユーザリクエストの受付、企業情報・株価予測データの提供、ニュース連携処理
  - **使用言語:** Ruby
  - **主なライブラリ/フレームワーク:**
    - Ruby on Rails
    - API 認証、ルーティングなどのGem群

- **データ取得・前処理サービス**
  - **機能:** 
    - 外部 API（Yahoo Finance など）から企業データの収集
    - NewsAPI や Google News API からリアルタイムニュースの取得
    - 取得データのクレンジング、感情分析、要約、キーフレーズ抽出
  - **使用言語:** Python
  - **主なライブラリ:**
    - Pandas, NumPy
    - Hugging Face Transformers

- **株価予測モデル & MLOps パイプライン**
  - **機能:** 
    - 汎用モデルの保存および、企業ごとのファインチューニング
    - 継続的再学習（定期バッチを想定）
    - ニュース情報を特徴量として株価予測に反映
  - **使用言語:** Python
  - **主なライブラリ/フレームワーク:**
    - PyTorch
    - MLflow, Apache Airflow

- **LLM（大規模言語モデル）による説明生成モジュール**
  - **機能:** ニュース情報と株価動向を紐付け、「なぜ株がこのような動きをするのか」を解説するテキスト生成
  - **使用言語:** Python
  - **主なライブラリ/フレームワーク:**
    - OpenAI API (GPT-4, ChatGPT API) または Hugging Face の LLM

- **コンテナ化・オーケストレーション & CI/CD**
  - **機能:** 各コンポーネントの分離、環境一貫性の確保、スケーラブルな運用
  - **技術:** Docker, Kubernetes
  - **CI/CD ツール:** GitHub Actions
  - **モニタリング:** Prometheus, Grafana, ELK Stack

---

## 2. 機能と使用言語／ライブラリの対応表

| 機能カテゴリ | 主な機能内容 | 使用言語 | 主なライブラリ／フレームワーク |
|------------|------------|---------|---------------------------|
| **フロントエンド** | ユーザ向けダッシュボード、企業指定、予測結果・解説の表示 | TypeScript | React / Next.js |
| **バックエンド API** | API 経由でのデータ連携、企業情報提供、ユーザ認証 | Ruby | Ruby on Rails / Sinatra, 各種 API 認証・ルーティング用 Gem |
| **データ取得・前処理** | 企業・ニュースデータの収集と前処理（感情分析、要約、キーフレーズ抽出）| Python | Pandas, NumPy, Hugging Face Transformers |
| **株価予測モデル & MLOps** | 汎用モデルのファインチューニング、継続的再学習、ニュース情報の統合 | Python | TensorFlow / PyTorch, MLflow, Apache Airflow |
| **LLM 説明生成** | ニュースと株価データから動向解説テキストの生成 | Python | OpenAI API / Hugging Face LLM, spaCy, Transformers |
| **コンテナ化・オーケストレーション** | 各コンポーネントの分離とスケール管理 | - | Docker |
| **CI/CD とモニタリング** | 自動テスト、デプロイ、ログ/メトリクスの収集・監視 | - | GitHub Actions, Prometheus, Grafana, ELK Stack |

## 3. アーキテクチャ概要

```mermaid
flowchart LR
  subgraph Frontend
    FE["Next.js (TypeScript)"]
  end

  subgraph Backend
    BE["Rails API"]
    DB[(Postgres)]
    BE --> DB
  end

  subgraph MLOps
    MLflow["MLflow／定期学習バッチ"]
    Sage["Amazon SageMaker（推論）"]
    S3[(S3 バケット)]
    MLflow --> Sage
    Sage --> S3
    BE --> S3
  end

  subgraph Explanation
    LLM["OpenAI API / Hugging Face LLM"]
    BE --> LLM
  end

  FE --> BE