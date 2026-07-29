from __future__ import annotations

import os
from pathlib import Path

from infrastructure.s3_storage import download_file


def main() -> None:
    bucket = os.environ["S3_BUCKET_NAME"]

    public_dataset_key = os.environ["PUBLIC_DATASET_KEY"]
    synthetic_dataset_key = os.environ["SYNTHETIC_DATASET_KEY"]

    data_dir = Path(os.getenv("LOCAL_DATA_DIR", "/tmp/data"))
    data_dir.mkdir(parents=True, exist_ok=True)

    public_dataset_path = data_dir / "public_it_tickets.csv"
    synthetic_dataset_path = data_dir / "synthetic_tickets.csv"

    download_file(
        bucket=bucket,
        key=public_dataset_key,
        local_path=public_dataset_path,
    )

    download_file(
        bucket=bucket,
        key=synthetic_dataset_key,
        local_path=synthetic_dataset_path,
    )

    if not public_dataset_path.is_file():
        raise RuntimeError(
            f"Public dataset was not downloaded to {public_dataset_path}"
        )

    if not synthetic_dataset_path.is_file():
        raise RuntimeError(
            f"Synthetic dataset was not downloaded to {synthetic_dataset_path}"
        )

    print(f"Downloaded public dataset to {public_dataset_path}")
    print(f"Downloaded synthetic dataset to {synthetic_dataset_path}")


if __name__ == "__main__":
    main()