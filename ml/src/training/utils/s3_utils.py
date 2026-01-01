# ml/src/training/utils/s3_utils.py

"""
S3アップロード用ユーティリティ
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional
import mimetypes


def upload_to_s3(
    local_path: Path,
    bucket: str,
    s3_key: str,
    content_type: Optional[str] = None,
) -> bool:
    """
    ファイルをS3にアップロード

    Args:
        local_path: ローカルファイルパス
        bucket: S3バケット名
        s3_key: S3キー
        content_type: Content-Type

    Returns:
        success: アップロード成功したか
    """
    try:
        import boto3

        s3_client = boto3.client("s3")

        # Content-Typeの推定
        if content_type is None:
            content_type, _ = mimetypes.guess_type(str(local_path))
            if content_type is None:
                content_type = "application/octet-stream"

        # アップロード
        s3_client.upload_file(
            str(local_path),
            bucket,
            s3_key,
            ExtraArgs={"ContentType": content_type},
        )

        print(f"[OK] Uploaded to s3://{bucket}/{s3_key}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to upload to S3: {e}")
        import traceback
        traceback.print_exc()
        return False


def upload_directory_to_s3(
    local_dir: Path,
    bucket: str,
    s3_prefix: str,
) -> bool:
    """
    ディレクトリをS3にアップロード

    Args:
        local_dir: ローカルディレクトリパス
        bucket: S3バケット名
        s3_prefix: S3プレフィックス

    Returns:
        success: アップロード成功したか
    """
    try:
        import boto3

        s3_client = boto3.client("s3")

        # ディレクトリ内のすべてのファイルをアップロード
        for file_path in local_dir.rglob("*"):
            if file_path.is_file():
                # 相対パスを取得
                relative_path = file_path.relative_to(local_dir)
                s3_key = f"{s3_prefix}/{relative_path}"

                # Content-Typeの推定
                content_type, _ = mimetypes.guess_type(str(file_path))
                if content_type is None:
                    content_type = "application/octet-stream"

                # アップロード
                s3_client.upload_file(
                    str(file_path),
                    bucket,
                    s3_key,
                    ExtraArgs={"ContentType": content_type},
                )

                print(f"[OK] Uploaded to s3://{bucket}/{s3_key}")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to upload directory to S3: {e}")
        import traceback
        traceback.print_exc()
        return False
