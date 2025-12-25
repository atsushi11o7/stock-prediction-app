# ml/src/data/utils/config.py
"""
設定ファイル処理の統一モジュール

すべてのスクリプトはこのモジュールの関数を使用して設定を読み込む。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


@dataclass(frozen=True)
class RetryConfig:
    times: int = 3
    sleep_seconds: float = 1.0


def load_yaml(path: Path) -> Dict[str, Any]:
    """
    YAML ファイルを読み込む

    Args:
        path (Path): 読み込むファイルのパス
    Returns:
        Dict[str, Any]: 読み込んだ YAML データ
    """
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_config(path: Path) -> Dict[str, Any]:
    """
    設定ファイルを読み込む（load_yaml のエイリアス）

    Args:
        path (Path): 読み込む設定ファイルのパス
    Returns:
        Dict[str, Any]: 読み込んだ設定データ
    """
    return load_yaml(path)


def get_base_dir(config_path: Path) -> Path:
    """
    設定ファイルのパスからベースディレクトリ（ml/）を取得

    Args:
        config_path: 設定ファイルのパス（例: /workspace/ml/config/train.yaml）
    Returns:
        Path: ベースディレクトリ（例: /workspace/ml）
    """
    return config_path.parent.parent


def get_env_config(cfg: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    環境設定を取得

    Args:
        cfg: 全体設定

    Returns:
        Tuple[env, env_cfg, input_cfg, output_cfg]
    """
    env = cfg.get("env", "local")
    env_cfg = cfg.get(env, {})
    input_cfg = env_cfg.get("input", {})
    output_cfg = env_cfg.get("output", {})
    return env, env_cfg, input_cfg, output_cfg


def resolve_path(path_str: str, base_dir: Path) -> Path:
    """
    相対パスをbase_dirからの絶対パスに解決

    Args:
        path_str: パス文字列
        base_dir: ベースディレクトリ

    Returns:
        Path: 解決されたパス
    """
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()

def parse_as_of(as_of: str) -> Optional[date]:
    """
    "auto" なら None、それ以外は YYYY-MM-DD 形式の日付文字列を date に変換して返す

    Args:
        as_of (str): 日付文字列または "auto"
    Returns:
        Optional[date]: 変換した日付、または None
    Raises:
        ValueError: 日付文字列のフォーマットが不正な場合
    """
    if as_of.lower() == "auto":
        return None
    try:
        return datetime.strptime(as_of, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(
            f"Invalid date format: '{as_of}'. Expected 'auto' or 'YYYY-MM-DD' format (e.g., '2025-12-18')"
        ) from e

def resolve_universe_yaml_path(cfg: Dict[str, Any], config_path: Path) -> Path:
    """
    universe YAML のパスを解決する（ローカル環境用）

    優先順位:
    1. local.input.universe_path
    2. universe_path（トップレベル）

    Args:
        cfg (Dict[str, Any]): 全体の設定辞書
        config_path (Path): 現在の設定ファイルのパス
    Returns:
        path (Path): 解決した universe YAML のパス
    """
    base_dir = config_path.parent.parent  # ml/ ディレクトリ

    # 1. local.input.universe_path を優先
    local_cfg = cfg.get("local", {})
    input_cfg = local_cfg.get("input", {})
    universe_path = input_cfg.get("universe_path")

    # 2. フォールバック: トップレベルの universe_path
    if not universe_path:
        universe_path = cfg.get("universe_path")

    if universe_path:
        p = Path(str(universe_path))
        if p.is_absolute():
            return p
        return (base_dir / p).resolve()

    raise ValueError(
        "Universe not specified. Set 'local.input.universe_path' in config."
    )


def download_universe_from_s3(bucket: str, key: str, local_path: Optional[Path] = None) -> Path:
    """
    S3からuniverse YAMLをダウンロードしてローカルパスを返す

    Args:
        bucket: S3バケット名
        key: S3キー（例: "config/universes/enrich_topix_core_30_20251031.yaml"）
        local_path: ローカル保存先パス（省略時は/tmp/に保存）

    Returns:
        Path: ダウンロードしたファイルのローカルパス
    """
    import boto3

    if local_path is None:
        filename = key.split("/")[-1]
        local_path = Path("/tmp") / filename

    s3_client = boto3.client('s3')
    s3_client.download_file(bucket, key, str(local_path))

    return local_path


def resolve_universe_yaml_path_with_s3(
    cfg: Dict[str, Any],
    config_path: Path,
) -> Path:
    """
    環境に応じてuniverse YAMLのパスを解決する

    - env: "local" の場合: ローカルファイルシステムから読み込み
    - env: "s3" の場合: S3からダウンロードしてローカルパスを返す

    Args:
        cfg: 設定辞書
        config_path: 設定ファイルのパス

    Returns:
        Path: universe YAMLのローカルパス
    """
    env = cfg.get("env", "local")

    if env == "s3":
        s3_cfg = cfg.get("s3", {})
        bucket = s3_cfg.get("bucket")
        input_cfg = s3_cfg.get("input", {})
        universe_key = input_cfg.get("universe_key")

        if not bucket or not universe_key:
            raise ValueError(
                "S3 environment requires 's3.bucket' and 's3.input.universe_key' in config"
            )

        return download_universe_from_s3(bucket, universe_key)
    else:
        # ローカル環境
        return resolve_universe_yaml_path(cfg, config_path)


def upload_universe_to_s3(local_path: Path, bucket: str, key: str) -> None:
    """
    universe YAMLをS3にアップロード

    Args:
        local_path: ローカルファイルパス
        bucket: S3バケット名
        key: S3キー
    """
    import boto3

    s3_client = boto3.client('s3')
    s3_client.upload_file(str(local_path), bucket, key)
    print(f"[INFO] Uploaded to s3://{bucket}/{key}")
