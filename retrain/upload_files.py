import os
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.s3_storage import upload_file


def main() -> None:
    bucket = os.environ["S3_BUCKET_NAME"]
    synthetic_key = os.environ["SYNTHETIC_DATASET_KEY"]

    data_dir = Path(
        os.getenv("LOCAL_DATA_DIR", "/tmp/data")
    )

    synthetic_file = data_dir / "synthetic_tickets.csv"
    validation_file = data_dir / "validation_output.txt"

    if not synthetic_file.is_file():
        raise FileNotFoundError(
            f"Synthetic dataset not found: {synthetic_file}"
        )

    upload_file(
        local_path=synthetic_file,
        bucket=bucket,
        key=synthetic_key,
    )

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    versions_prefix = os.getenv(
        "DATASET_VERSIONS_PREFIX",
        "datasets/versions/",
    ).rstrip("/")

    versioned_key = (
        f"{versions_prefix}/"
        f"synthetic-tickets-{timestamp}.csv"
    )

    upload_file(
        local_path=synthetic_file,
        bucket=bucket,
        key=versioned_key,
    )

    if validation_file.is_file():
        reports_prefix = os.getenv(
            "VALIDATION_REPORTS_PREFIX",
            "reports/validation/",
        ).rstrip("/")

        report_key = (
            f"{reports_prefix}/"
            f"synthetic-validation-{timestamp}.txt"
        )

        upload_file(
            local_path=validation_file,
            bucket=bucket,
            key=report_key,
        )

    print(
        f"Updated synthetic dataset at "
        f"s3://{bucket}/{synthetic_key}"
    )
    print(
        f"Uploaded dataset version to "
        f"s3://{bucket}/{versioned_key}"
    )


if __name__ == "__main__":
    main()