# ml/src/data/utils/s3io.py
from __future__ import annotations

import json
from typing import Any, Dict

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    boto3 = None
    BotoCoreError = None
    ClientError = None


def put_json(bucket: str, key: str, payload: Dict[str, Any], indent: int = 2) -> None:
    """
    S3 に JSON ファイルを書き出す

    Args:
        bucket (str): S3 バケット名
        key (str): S3 オブジェクトキー
        payload (Dict[str, Any]): 書き出す JSON データ
        indent (int): JSONのインデント（デフォルト: 2）

    Returns:
        None

    Raises:
        RuntimeError: boto3がインストールされていない場合
        ClientError: S3への書き込みが失敗した場合
    """
    if boto3 is None:
        raise RuntimeError(
            "boto3 is not installed but S3 output is enabled. "
            "Install it with: pip install boto3"
        )

    try:
        s3 = boto3.client("s3")
        body = json.dumps(payload, ensure_ascii=False, indent=indent).encode("utf-8")
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType="application/json; charset=utf-8",
        )
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(
            f"Failed to upload to S3: s3://{bucket}/{key}. Error: {e}"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Unexpected error while uploading to S3: s3://{bucket}/{key}. Error: {e}"
        ) from e
