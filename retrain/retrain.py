import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

from infrastructure.s3_storage import download_file


load_dotenv()

DATA_DIR = Path(os.getenv("LOCAL_DATA_DIR", "/tmp/data"))
SYNTHETIC_FILE = DATA_DIR / "synthetic_tickets.csv"


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        sslmode=os.getenv("DB_SSLMODE", "require"),
    )


def retrain_model():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    bucket = os.environ["S3_BUCKET_NAME"]
    synthetic_key = os.environ["SYNTHETIC_DATASET_KEY"]
    minimum_records = int(os.getenv("RETRAIN_MIN_RECORDS", "5"))

    download_file(
        bucket=bucket,
        key=synthetic_key,
        local_path=SYNTHETIC_FILE,
    )

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT COUNT(*)
            FROM tickets
            WHERE confirmed_category IS NOT NULL
              AND used_for_training IS FALSE
            """
        )

        count = cur.fetchone()[0]

        if count < minimum_records:
            print(
                f"Only {count} eligible tickets found. "
                f"At least {minimum_records} are required."
            )
            return

        cur.execute(
            """
            SELECT
                ticket_id AS "Ticket ID",
                confirmed_category AS "Category",
                subcategory AS "Subcategory",
                priority AS "Priority",
                description AS "Description",
                source AS "Source"
            FROM tickets
            WHERE confirmed_category IS NOT NULL
              AND used_for_training IS FALSE
            """
        )

        rows = cur.fetchall()
        ticket_ids = [row[0] for row in rows]
        columns = [description[0] for description in cur.description]

        new_data = pd.DataFrame(rows, columns=columns)

        synthetic_data = pd.read_csv(
            SYNTHETIC_FILE,
            dtype=str,
        ).fillna("")

        synthetic_data = pd.concat(
            [synthetic_data, new_data],
            ignore_index=True,
        )

        synthetic_data.to_csv(
            SYNTHETIC_FILE,
            index=False,
        )

        cur.execute(
            """
            UPDATE tickets
            SET used_for_training = TRUE
            WHERE ticket_id = ANY(%s)
            """,
            (ticket_ids,),
        )

        conn.commit()

        print(
            f"Added {len(new_data)} tickets to "
            f"{SYNTHETIC_FILE}"
        )

    except Exception:
        if conn:
            conn.rollback()
        raise

    finally:
        if cur is not None:
            cur.close()

        if conn is not None:
            conn.close()


if __name__ == "__main__":
    retrain_model()