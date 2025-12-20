"""
統一されたログ設定モジュール
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    統一されたロガーを設定

    Args:
        name: ロガー名（通常は__name__を使用）
        level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        format_string: カスタムフォーマット文字列（Noneの場合はデフォルト）

    Returns:
        logging.Logger: 設定済みロガー

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Processing started")
        2025-12-20 12:34:56 - __main__ - INFO - Processing started
    """
    logger = logging.getLogger(name)

    # 既にハンドラーがある場合は追加しない（重複防止）
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # コンソールハンドラー
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # フォーマット
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    formatter = logging.Formatter(
        format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def setup_simple_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    シンプルなフォーマットのロガーを設定（タイムスタンプなし）

    Args:
        name: ロガー名
        level: ログレベル

    Returns:
        logging.Logger: 設定済みロガー

    Example:
        >>> logger = setup_simple_logger(__name__)
        >>> logger.info("Processing started")
        INFO - Processing started
    """
    return setup_logger(
        name,
        level,
        format_string='%(levelname)s - %(message)s'
    )
