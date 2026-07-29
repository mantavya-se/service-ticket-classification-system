from __future__ import annotations
import logging
from pathlib import Path 
import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

s3 = boto3.client("s3")

def download_file(bucket: str, key: str, local_path: str | Path) -> Path:
    destination = Path(local_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info("Downloading s3://%s/%s to %s", bucket, key, destination)
        s3.download_file(bucket, key, str(destination))

    except (ClientError, BotoCoreError) as err:
        raise RuntimeError(f"Failed to download s3://{bucket}/{key}") from err

    return destination


def upload_file(local_path: str | Path, bucket: str, key: str) -> None:
    source = Path(local_path)

    if not source.is_file():
        raise  FileNotFoundError(f"Upload Source does not exist: {source}")

    try:
        logger.info("Uploading %s to s3://%s/%s", source, bucket, key)
        s3.upload_file(str(source), bucket, key)

    except (ClientError, BotoCoreError) as err:
        raise RuntimeError(f"Failed to upload {source} to s3://{bucket}/{key}") from err

def download_folder(bucket: str, prefix: str, local_directory: str | Path) -> list[Path]:
    destination = Path(local_directory)
    destination.mkdir(parents=True, exist_ok=True)

    paginator = s3.get_paginator("list_objects_v2")
    downloaded: list[Path] = []

    try:
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

        for page in pages:
            for item in page.get("Contents", []):
                key = item["key"]

                if key.endswith("/"):
                    continue

                relative_key = key.remove_prefix(prefix).lstrip("/")
                local_path = destination / relative_key
                local_path.parent.mkdir(parents=True, exist_ok=True)

                s3.download_file(bucket, key, str(local_path))

                downloaded.append(local_path)

    except (ClientError, BotoCoreError) as err:
        raise RuntimeError(f"Failed to download s3://{bucket}/{prefix}") from err


    return downloaded
