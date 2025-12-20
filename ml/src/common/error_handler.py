"""
統一されたエラーハンドリングモジュール
"""

import logging
from typing import List, Callable, Any, Optional
from pathlib import Path


def handle_ticker_error(
    ticker: str,
    error: Exception,
    logger: logging.Logger,
    context: Optional[str] = None,
) -> str:
    """
    ティッカー処理エラーの統一ハンドラー

    Args:
        ticker: ティッカーシンボル
        error: 発生した例外
        logger: ロガーインスタンス
        context: エラーコンテキスト（例: "fetching data", "calculating features"）

    Returns:
        str: フォーマットされたエラーメッセージ

    Example:
        >>> try:
        ...     process_ticker("AAPL")
        ... except Exception as e:
        ...     error_msg = handle_ticker_error("AAPL", e, logger, "fetching data")
        ...     failed_tickers.append(error_msg)
    """
    error_type = type(error).__name__
    error_msg = str(error)

    if context:
        full_msg = f"{ticker} ({context}): {error_type}: {error_msg}"
    else:
        full_msg = f"{ticker}: {error_type}: {error_msg}"

    logger.error(full_msg)
    return full_msg


def process_tickers_with_error_handling(
    tickers: List[str],
    process_func: Callable[[str], Any],
    logger: logging.Logger,
    context: Optional[str] = None,
) -> tuple[List[Any], List[str]]:
    """
    ティッカーリストを処理し、成功と失敗を分離

    Args:
        tickers: ティッカーリスト
        process_func: 各ティッカーを処理する関数
        logger: ロガーインスタンス
        context: エラーコンテキスト

    Returns:
        tuple[List[Any], List[str]]: (成功結果リスト, エラーメッセージリスト)

    Example:
        >>> def fetch_data(ticker: str) -> dict:
        ...     # データ取得処理
        ...     return {"ticker": ticker, "data": ...}
        >>>
        >>> results, errors = process_tickers_with_error_handling(
        ...     tickers=["AAPL", "GOOGL", "MSFT"],
        ...     process_func=fetch_data,
        ...     logger=logger,
        ...     context="fetching data"
        ... )
    """
    results = []
    errors = []

    for ticker in tickers:
        try:
            result = process_func(ticker)
            results.append(result)
        except Exception as e:
            error_msg = handle_ticker_error(ticker, e, logger, context)
            errors.append(error_msg)

    return results, errors


def validate_file_exists(file_path: Path, file_description: str = "File") -> None:
    """
    ファイルの存在を確認し、存在しない場合は例外を発生

    Args:
        file_path: 確認するファイルパス
        file_description: ファイルの説明（エラーメッセージ用）

    Raises:
        FileNotFoundError: ファイルが存在しない場合

    Example:
        >>> validate_file_exists(Path("model.onnx"), "ONNX model")
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"{file_description} not found: {file_path}\n"
            f"Please ensure the file exists before running."
        )


def validate_directory_exists(dir_path: Path, dir_description: str = "Directory") -> None:
    """
    ディレクトリの存在を確認し、存在しない場合は例外を発生

    Args:
        dir_path: 確認するディレクトリパス
        dir_description: ディレクトリの説明（エラーメッセージ用）

    Raises:
        NotADirectoryError: ディレクトリが存在しない場合

    Example:
        >>> validate_directory_exists(Path("data/training/daily"), "Daily data directory")
    """
    if not dir_path.exists():
        raise NotADirectoryError(
            f"{dir_description} not found: {dir_path}\n"
            f"Please ensure the directory exists before running."
        )
    if not dir_path.is_dir():
        raise NotADirectoryError(
            f"{dir_description} is not a directory: {dir_path}"
        )
