from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.s3_storage import upload_file


def main() -> None:
    bucket = os.environ["S3_BUCKET_NAME"]

    combined_dataset_key = os.environ["COMBINED_DATASET_KEY"]
    model_production_key = os.environ["MODEL_PRODUCTION_KEY"]
    model_versions_prefix = os.environ["MODEL_VERSIONS_PREFIX"].rstrip("/")

    data_dir = Path(os.getenv("LOCAL_DATA_DIR", "/tmp/data"))
    model_dir = Path(os.getenv("LOCAL_MODEL_DIR", "/tmp/models"))

    combined_dataset_path = data_dir / "combined_ticket.csv"
    model_path = model_dir / "ticket-classifier.joblib"

    if not combined_dataset_path.is_file():
        raise FileNotFoundError(
            f"Combined dataset does not exist: {combined_dataset_path}"
        )

    if not model_path.is_file():
        raise FileNotFoundError(
            f"Trained model does not exist: {model_path}"
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    versioned_model_key = (
        f"{model_versions_prefix}/"
        f"ticket-classifier-{timestamp}.joblib"
    )

    # Upload the generated combined dataset.
    upload_file(
        local_path=combined_dataset_path,
        bucket=bucket,
        key=combined_dataset_key,
    )

    # Store an immutable/versioned model first.
    upload_file(
        local_path=model_path,
        bucket=bucket,
        key=versioned_model_key,
    )

    # Update the model currently used by the API last.
    upload_file(
        local_path=model_path,
        bucket=bucket,
        key=model_production_key,
    )

    print(
        f"Uploaded combined dataset to "
        f"s3://{bucket}/{combined_dataset_key}"
    )
    print(
        f"Uploaded versioned model to "
        f"s3://{bucket}/{versioned_model_key}"
    )
    print(
        f"Updated production model at "
        f"s3://{bucket}/{model_production_key}"
    )


if __name__ == "__main__":
    main()