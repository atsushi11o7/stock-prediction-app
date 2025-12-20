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
    universe YAML のパスを解決する

    Args:
        cfg (Dict[str, Any]): 全体の設定辞書
        config_path (Path): 現在の設定ファイルのパス
    Returns:
        path (Path): 解決した universe YAML のパス
    """
    if cfg.get("universe_path"):
        p = Path(str(cfg["universe_path"]))
        return p if p.is_absolute() else (config_path.parent / p).resolve()

    defaults = cfg.get("defaults", [])
    universe_name: Optional[str] = None
    if isinstance(defaults, list):
        for d in defaults:
            if isinstance(d, dict) and "universes" in d:
                universe_name = d["universes"]
                break

    if not universe_name:
        raise ValueError("Universe not specified. Set `universe_path:` or `defaults: - universes: <name>`.")

    return (config_path.parent / "universes" / f"{universe_name}.yaml").resolve()
