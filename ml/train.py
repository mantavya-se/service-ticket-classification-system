from datetime import datetime, timezone
from pathlib import Path
import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from infrastructure.s3_storage import download_file, upload_file

MODEL_DIR = Path("/tmp/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_FILE = MODEL_DIR / "ticket-classifier.joblib"

DATA_FILE = Path("/tmp/data/combined_ticket.csv")

df = pd.read_csv(DATA_FILE, dtype=str).fillna("")

X = df["Subcategory"] + " " + df["Description"]
y = df["Category"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

category_classifier = Pipeline(
    [
        (
            "vectorizer",
            TfidfVectorizer(
                sublinear_tf=True,
                max_df=0.9,
                min_df=2,
                ngram_range=(1, 2),
            ),
        ),
        (
            "model",
            LogisticRegression(max_iter=1000),
        ),
    ]
)

category_classifier.fit(X_train, y_train)

predictions = category_classifier.predict(X_test)

print(f"Accuracy: {accuracy_score(y_test, predictions)}")
print(classification_report(y_test, predictions))

joblib.dump(category_classifier, MODEL_FILE)

timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

versions_prefix = os.environ["MODEL_VERSIONS_PREFIX"].rstrip("/")

versioned_key = (
    f"{versions_prefix}/"
    f"ticket-classifier-{timestamp}.joblib"
)

upload_file(
    local_path=MODEL_FILE,
    bucket=os.environ["S3_BUCKET_NAME"],
    key=versioned_key,
)

upload_file(
    local_path=MODEL_FILE,
    bucket=os.environ["S3_BUCKET_NAME"],
    key=os.environ["MODEL_PRODUCTION_KEY"],
)

print(f"Uploaded versioned model to {versioned_key}")
print(
    "Updated production model at "
    f"{os.environ['MODEL_PRODUCTION_KEY']}"
)