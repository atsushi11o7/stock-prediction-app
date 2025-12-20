"""
統一されたS3操作モジュール
"""

import io
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator
from datetime import datetime


def parse_s3_uri(uri: str) -> tuple:
    """
    S3 URIをバケット名とキーに分解

    Args:
        uri: S3 URI (例: "s3://bucket/prefix/file.json")

    Returns:
        tuple: (bucket, key)

    Example:
        >>> bucket, key = parse_s3_uri("s3://my-bucket/data/file.json")
        >>> print(bucket, key)
        'my-bucket' 'data/file.json'
    """
    if not uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {uri}")

    path = uri[5:]  # Remove "s3://"
    parts = path.split("/", 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ""
    return bucket, key


def is_s3_path(path: str) -> bool:
    """パスがS3パスかどうかを判定"""
    return path.startswith("s3://")


def list_s3_objects(
    bucket: str,
    prefix: str,
    suffix: str = ".json",
    logger: Optional[logging.Logger] = None,
) -> List[str]:
    """
    S3バケット内のオブジェクトをリスト

    Args:
        bucket: S3バケット名
        prefix: S3キープレフィックス
        suffix: ファイル拡張子でフィルタ
        logger: ロガーインスタンス

    Returns:
        List[str]: オブジェクトキーのリスト（ソート済み）
    """
    import boto3

    s3_client = boto3.client("s3")
    keys = []

    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(suffix):
                keys.append(key)

    keys.sort()
    if logger:
        logger.debug(f"Found {len(keys)} objects in s3://{bucket}/{prefix}")

    return keys


def read_s3_json(bucket: str, key: str) -> Dict[str, Any]:
    """
    S3からJSONファイルを読み込む

    Args:
        bucket: S3バケット名
        key: S3オブジェクトキー

    Returns:
        Dict: JSONデータ
    """
    import boto3

    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read().decode("utf-8")
    return json.loads(content)


def iter_s3_json_files(
    bucket: str,
    prefix: str,
    suffix: str = ".json",
    logger: Optional[logging.Logger] = None,
) -> Generator[tuple, None, None]:
    """
    S3バケット内のJSONファイルをイテレート

    Args:
        bucket: S3バケット名
        prefix: S3キープレフィックス
        suffix: ファイル拡張子でフィルタ
        logger: ロガーインスタンス

    Yields:
        tuple: (key, data) - S3キーとJSONデータ
    """
    keys = list_s3_objects(bucket, prefix, suffix, logger)

    for key in keys:
        try:
            data = read_s3_json(bucket, key)
            yield key, data
        except Exception as e:
            if logger:
                logger.warning(f"Failed to read s3://{bucket}/{key}: {e}")


def upload_with_latest(
    local_path: Path,
    bucket: str,
    key: str,
    latest_key: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> List[str]:
    """
    S3にファイルをアップロードし、オプションでlatest版も作成

    Args:
        local_path: ローカルファイルパス
        bucket: S3バケット名
        key: S3キー（パス）
        latest_key: latest版のS3キー（Noneの場合はlatest版を作成しない）
        logger: ロガーインスタンス（Noneの場合はログ出力なし）

    Returns:
        List[str]: アップロードされたS3 URIのリスト

    Raises:
        FileNotFoundError: ローカルファイルが存在しない場合
        Exception: S3アップロードに失敗した場合

    Example:
        >>> uploaded = upload_with_latest(
        ...     local_path=Path("predictions/latest.json"),
        ...     bucket="my-bucket",
        ...     key="predictions/predictions_20251220_120000.json",
        ...     latest_key="predictions/latest.json",
        ...     logger=logger
        ... )
        >>> print(uploaded)
        ['s3://my-bucket/predictions/predictions_20251220_120000.json',
         's3://my-bucket/predictions/latest.json']
    """
    import boto3

    if not local_path.exists():
        raise FileNotFoundError(f"Local file not found: {local_path}")

    s3_client = boto3.client("s3")
    uploaded_uris = []

    # Upload with timestamp/specific key
    s3_client.upload_file(
        str(local_path),
        bucket,
        key,
    )
    uri = f"s3://{bucket}/{key}"
    uploaded_uris.append(uri)

    if logger:
        logger.info(f"Uploaded to {uri}")

    # Upload as latest if specified
    if latest_key:
        s3_client.upload_file(
            str(local_path),
            bucket,
            latest_key,
        )
        latest_uri = f"s3://{bucket}/{latest_key}"
        uploaded_uris.append(latest_uri)

        if logger:
            logger.info(f"Uploaded to {latest_uri}")

    return uploaded_uris


def upload_checkpoint_to_s3(
    checkpoint_path: Path,
    bucket: str,
    prefix: str,
    upload_latest: bool = True,
    logger: Optional[logging.Logger] = None,
) -> List[str]:
    """
    PyTorchチェックポイントをS3にアップロード

    Args:
        checkpoint_path: チェックポイントファイルパス
        bucket: S3バケット名
        prefix: S3キープレフィックス（例: "checkpoints"）
        upload_latest: latest版もアップロードするか
        logger: ロガーインスタンス

    Returns:
        List[str]: アップロードされたS3 URIのリスト

    Example:
        >>> uploaded = upload_checkpoint_to_s3(
        ...     checkpoint_path=Path("checkpoints/best_model-epoch=20-val_loss=0.0110.ckpt"),
        ...     bucket="my-bucket",
        ...     prefix="checkpoints",
        ...     logger=logger
        ... )
    """
    filename = checkpoint_path.name
    key = f"{prefix}/{filename}"
    latest_key = f"{prefix}/latest.ckpt" if upload_latest else None

    return upload_with_latest(
        local_path=checkpoint_path,
        bucket=bucket,
        key=key,
        latest_key=latest_key,
        logger=logger,
    )


def upload_onnx_to_s3(
    onnx_path: Path,
    bucket: str,
    prefix: str,
    upload_latest: bool = True,
    upload_metadata: bool = True,
    logger: Optional[logging.Logger] = None,
) -> List[str]:
    """
    ONNXモデルとメタデータをS3にアップロード

    Args:
        onnx_path: ONNXモデルファイルパス
        bucket: S3バケット名
        prefix: S3キープレフィックス（例: "models/onnx"）
        upload_latest: latest版もアップロードするか
        upload_metadata: メタデータファイルもアップロードするか
        logger: ロガーインスタンス

    Returns:
        List[str]: アップロードされたS3 URIのリスト

    Example:
        >>> uploaded = upload_onnx_to_s3(
        ...     onnx_path=Path("models/onnx/model_20251220_120000.onnx"),
        ...     bucket="my-bucket",
        ...     prefix="models/onnx",
        ...     logger=logger
        ... )
    """
    uploaded_uris = []

    # Upload ONNX model
    filename = onnx_path.name
    key = f"{prefix}/{filename}"
    latest_key = f"{prefix}/latest.onnx" if upload_latest else None

    uploaded_uris.extend(
        upload_with_latest(
            local_path=onnx_path,
            bucket=bucket,
            key=key,
            latest_key=latest_key,
            logger=logger,
        )
    )

    # Upload metadata JSON if it exists
    if upload_metadata:
        metadata_path = onnx_path.with_suffix(".json")
        if metadata_path.exists():
            metadata_key = f"{prefix}/{metadata_path.name}"
            metadata_latest_key = f"{prefix}/latest.json" if upload_latest else None

            uploaded_uris.extend(
                upload_with_latest(
                    local_path=metadata_path,
                    bucket=bucket,
                    key=metadata_key,
                    latest_key=metadata_latest_key,
                    logger=logger,
                )
            )

    return uploaded_uris


def upload_predictions_to_s3(
    predictions_path: Path,
    bucket: str,
    prefix: str = "predictions",
    upload_latest: bool = True,
    logger: Optional[logging.Logger] = None,
) -> List[str]:
    """
    予測結果JSONをS3にアップロード

    Args:
        predictions_path: 予測結果JSONファイルパス
        bucket: S3バケット名
        prefix: S3キープレフィックス（例: "predictions"）
        upload_latest: latest版もアップロードするか
        logger: ロガーインスタンス

    Returns:
        List[str]: アップロードされたS3 URIのリスト

    Example:
        >>> uploaded = upload_predictions_to_s3(
        ...     predictions_path=Path("predictions/latest.json"),
        ...     bucket="my-bucket",
        ...     logger=logger
        ... )
    """
    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    key = f"{prefix}/predictions_{timestamp}.json"
    latest_key = f"{prefix}/latest.json" if upload_latest else None

    return upload_with_latest(
        local_path=predictions_path,
        bucket=bucket,
        key=key,
        latest_key=latest_key,
        logger=logger,
    )
