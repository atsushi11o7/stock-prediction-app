# ml/src/data/utils/io.py
"""
データ読み込み・書き込みの統一モジュール

すべてのスクリプトはこのモジュールを使用してデータI/Oを行う。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd


# =============================================================================
# 定数定義
# =============================================================================

# 標準カラムマッピング（小文字 → 大文字）
COLUMN_MAPPING = {
    "ticker": "Ticker",
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "adjclose": "AdjClose",
    "volume": "Volume",
}

# 必須カラム
REQUIRED_COLUMNS = ["Date", "Ticker", "Open", "High", "Low", "Close", "AdjClose", "Volume"]


def ensure_dir(p: Path) -> None:
    """
    ディレクトリがなければ作成する

    Args:
        p (Path): 作成するディレクトリのパス

    Returns:
        None

    Raises:
        OSError: ディレクトリの作成に失敗した場合
    """
    try:
        p.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OSError(f"Failed to create directory: {p}. Error: {e}") from e


def write_json(path: Path, payload: Dict[str, Any], indent: int = 2) -> None:
    """
    JSON ファイルを書き出す

    Args:
        path (Path): 書き出すファイルのパス
        payload (Dict[str, Any]): 書き出す JSON データ
        indent (int): JSONのインデント（デフォルト: 2）

    Returns:
        None

    Raises:
        OSError: ファイルの書き込みに失敗した場合
        TypeError: payloadがJSON serializable でない場合
    """
    try:
        content = json.dumps(payload, ensure_ascii=False, indent=indent)
        path.write_text(content, encoding="utf-8")
    except TypeError as e:
        raise TypeError(f"Payload is not JSON serializable: {e}") from e
    except OSError as e:
        raise OSError(f"Failed to write JSON to {path}. Error: {e}") from e


def write_daily_payloads(outdir: Path, day_str: str, payload: Dict[str, Any]) -> None:
    """
    日付ごとの JSON ファイルと latest.json を書き出す

    Args:
        outdir (Path): 書き出すディレクトリのパス
        day_str (str): 書き出す日付文字列（YYYY-MM-DD）
        payload (Dict[str, Any]): 書き出す JSON データ

    Returns:
        None

    Raises:
        OSError: ディレクトリ作成またはファイル書き込みに失敗した場合
        TypeError: payloadがJSON serializable でない場合
    """
    ensure_dir(outdir)
    write_json(outdir / f"{day_str}.json", payload)
    write_json(outdir / "latest.json", payload)


# =============================================================================
# 日次データ読み込み（統一インターフェース）
# =============================================================================

def load_daily_data_from_local(
    daily_data_dir: Path,
    lookback_days: Optional[int] = None,
    as_of_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    ローカルの日次JSONデータを読み込む

    Args:
        daily_data_dir: 日次データディレクトリ
        lookback_days: 遡る日数（Noneの場合は全データ）
        as_of_date: 基準日（Noneの場合は最新）

    Returns:
        DataFrame: 日次データ（Ticker, Dateでソート済み）
    """
    json_files = sorted(daily_data_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "latest.json"]

    if not json_files:
        raise ValueError(f"No JSON files found in {daily_data_dir}")

    # 日付フィルタリング
    if lookback_days is not None:
        if as_of_date:
            ref_date = datetime.strptime(as_of_date, "%Y-%m-%d")
        else:
            ref_date = datetime.now()
        cutoff_date = ref_date - timedelta(days=lookback_days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")

        filtered_files = []
        for f in json_files:
            try:
                file_date = f.stem  # "YYYY-MM-DD"
                if file_date >= cutoff_str:
                    if as_of_date is None or file_date <= as_of_date:
                        filtered_files.append(f)
            except Exception:
                continue
        json_files = filtered_files

    if not json_files:
        raise ValueError(f"No JSON files found after filtering in {daily_data_dir}")

    # データ読み込み
    records = []
    errors = []
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            date_str = data.get("as_of")
            if not date_str:
                errors.append(f"{json_file.name}: missing 'as_of' field")
                continue

            symbols = data.get("symbols", [])
            if not symbols:
                errors.append(f"{json_file.name}: no symbols data")
                continue

            for sym in symbols:
                sym["Date"] = date_str
                records.append(sym)
        except json.JSONDecodeError as e:
            errors.append(f"{json_file.name}: JSON parse error - {e}")
            continue
        except Exception as e:
            errors.append(f"{json_file.name}: {e}")
            continue

    if errors and len(errors) <= 5:
        import logging
        logger = logging.getLogger(__name__)
        for err in errors:
            logger.warning(f"Data loading warning: {err}")

    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"])

    # カラム名を標準化
    df = df.rename(columns=COLUMN_MAPPING)

    # 必須カラムの確認
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    return df.sort_values(["Ticker", "Date"]).reset_index(drop=True)


def load_daily_data_from_s3(
    bucket: str,
    prefix: str,
    lookback_days: Optional[int] = None,
    as_of_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    S3から日次JSONデータを読み込む

    Args:
        bucket: S3バケット名
        prefix: S3プレフィックス
        lookback_days: 遡る日数（Noneの場合は全データ）
        as_of_date: 基準日（Noneの場合は最新）

    Returns:
        DataFrame: 日次データ
    """
    import boto3

    s3_client = boto3.client("s3")

    # S3からファイル一覧を取得
    paginator = s3_client.get_paginator("list_objects_v2")
    json_files = []

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".json") and not key.endswith("latest.json"):
                json_files.append(key)

    json_files.sort()

    if not json_files:
        raise ValueError(f"No JSON files found in s3://{bucket}/{prefix}")

    # 日付フィルタリング
    if lookback_days is not None:
        if as_of_date:
            ref_date = datetime.strptime(as_of_date, "%Y-%m-%d")
        else:
            ref_date = datetime.now()
        cutoff_date = ref_date - timedelta(days=lookback_days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")

        filtered_files = []
        for key in json_files:
            try:
                filename = key.split("/")[-1]
                file_date = filename.replace(".json", "")
                if file_date >= cutoff_str:
                    if as_of_date is None or file_date <= as_of_date:
                        filtered_files.append(key)
            except Exception:
                continue
        json_files = filtered_files

    # データ読み込み
    records = []
    for key in json_files:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        data = json.loads(response["Body"].read().decode("utf-8"))

        date_str = data.get("as_of")
        symbols = data.get("symbols", [])

        for sym in symbols:
            sym["Date"] = date_str
            records.append(sym)

    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"])

    # カラム名を標準化
    df = df.rename(columns=COLUMN_MAPPING)

    return df.sort_values(["Ticker", "Date"]).reset_index(drop=True)


def load_daily_data(
    source: str,
    path_or_prefix: str,
    bucket: Optional[str] = None,
    lookback_days: Optional[int] = None,
    as_of_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    データソースに応じて日次データを読み込む（統一インターフェース）

    Args:
        source: "local" または "s3"
        path_or_prefix: ローカルパスまたはS3プレフィックス
        bucket: S3バケット名（source="s3"の場合に必須）
        lookback_days: 遡る日数（Noneの場合は全データ）
        as_of_date: 基準日（Noneの場合は最新）

    Returns:
        DataFrame: 日次データ
    """
    if source == "local":
        return load_daily_data_from_local(
            daily_data_dir=Path(path_or_prefix),
            lookback_days=lookback_days,
            as_of_date=as_of_date,
        )
    elif source == "s3":
        if not bucket:
            raise ValueError("bucket is required for S3 source")
        return load_daily_data_from_s3(
            bucket=bucket,
            prefix=path_or_prefix,
            lookback_days=lookback_days,
            as_of_date=as_of_date,
        )
    else:
        raise ValueError(f"Unknown source: {source}. Must be 'local' or 's3'")


def load_daily_data_for_ticker(
    daily_data_path: str,
    ticker: str,
) -> pd.DataFrame:
    """
    指定した銘柄の日次データを読み込む（推論用）

    ローカルパスとS3 URIの両方に対応。

    Args:
        daily_data_path: ローカルパスまたはS3 URI (e.g., "s3://bucket/prefix")
        ticker: 銘柄ティッカー

    Returns:
        DataFrame: 指定銘柄の日次データ
    """
    if daily_data_path.startswith("s3://"):
        return _load_daily_data_for_ticker_from_s3(daily_data_path, ticker)
    else:
        return _load_daily_data_for_ticker_from_local(Path(daily_data_path), ticker)


def _load_daily_data_for_ticker_from_local(
    daily_data_dir: Path,
    ticker: str,
) -> pd.DataFrame:
    """ローカルから指定銘柄の日次データを読み込む"""
    json_files = sorted(daily_data_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "latest.json"]

    if not json_files:
        raise FileNotFoundError(f"No daily data files found in: {daily_data_dir}")

    records = []
    for json_path in json_files:
        with open(json_path, "r", encoding="utf-8") as f:
            daily_data = json.load(f)

        as_of_date = daily_data.get("as_of")
        if not as_of_date:
            as_of_date = json_path.stem

        symbols = daily_data.get("symbols", [])
        for symbol in symbols:
            if symbol.get("ticker") == ticker:
                record = {
                    "Date": as_of_date,
                    "Ticker": ticker,
                    "Open": symbol.get("open"),
                    "High": symbol.get("high"),
                    "Low": symbol.get("low"),
                    "Close": symbol.get("close"),
                    "AdjClose": symbol.get("adjclose"),
                    "Volume": symbol.get("volume"),
                }
                records.append(record)
                break

    if not records:
        raise ValueError(f"No data found for ticker: {ticker}")

    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values("Date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def _load_daily_data_for_ticker_from_s3(
    s3_uri: str,
    ticker: str,
) -> pd.DataFrame:
    """S3から指定銘柄の日次データを読み込む"""
    import boto3

    # Parse S3 URI
    if not s3_uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {s3_uri}")

    parts = s3_uri[5:].split("/", 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ""

    s3_client = boto3.client("s3")

    # S3からファイル一覧を取得
    paginator = s3_client.get_paginator("list_objects_v2")
    json_keys = []

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".json") and not key.endswith("latest.json"):
                json_keys.append(key)

    json_keys.sort()

    if not json_keys:
        raise FileNotFoundError(f"No daily data files found in: {s3_uri}")

    records = []
    for key in json_keys:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        daily_data = json.loads(response["Body"].read().decode("utf-8"))

        as_of_date = daily_data.get("as_of")
        if not as_of_date:
            filename = key.split("/")[-1]
            as_of_date = filename.replace(".json", "")

        symbols = daily_data.get("symbols", [])
        for symbol in symbols:
            if symbol.get("ticker") == ticker:
                record = {
                    "Date": as_of_date,
                    "Ticker": ticker,
                    "Open": symbol.get("open"),
                    "High": symbol.get("high"),
                    "Low": symbol.get("low"),
                    "Close": symbol.get("close"),
                    "AdjClose": symbol.get("adjclose"),
                    "Volume": symbol.get("volume"),
                }
                records.append(record)
                break

    if not records:
        raise ValueError(f"No data found for ticker: {ticker} in {s3_uri}")

    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values("Date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df
