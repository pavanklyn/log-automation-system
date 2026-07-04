"""
s3_uploader.py

Uploads archived log files (.gz) to an S3 bucket. Uses standard boto3
credential resolution (env vars, ~/.aws/credentials, or IAM role) — no
credentials are read from config.yaml.
"""

from __future__ import annotations

from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def upload_files(paths: list[Path], bucket_name: str, region: str, prefix: str = "logs/") -> list[str]:
    """Upload each file to S3 under `prefix`. Returns list of successfully
    uploaded S3 keys."""
    s3 = boto3.client("s3", region_name=region)
    uploaded = []

    for path in paths:
        key = f"{prefix}{path.name}"
        try:
            s3.upload_file(str(path), bucket_name, key)
            uploaded.append(key)
            print(f"[s3_uploader] Uploaded {path.name} -> s3://{bucket_name}/{key}")
        except (BotoCoreError, ClientError) as e:
            print(f"[s3_uploader] Failed to upload {path.name}: {e}")

    return uploaded
