import os
from pathlib import Path

import joblib

from infrastructure.s3_storage import download_file


MODEL_BUCKET = os.environ["MODEL_S3_BUCKET"]
MODEL_KEY = os.environ["MODEL_S3_KEY"]
MODEL_LOCAL_PATH = Path(
    os.getenv("MODEL_LOCAL_PATH", "/tmp/ticket-classifier.joblib")
)


def load_model():
    download_file(
        bucket=MODEL_BUCKET,
        key=MODEL_KEY,
        local_path=MODEL_LOCAL_PATH,
    )

    return joblib.load(MODEL_LOCAL_PATH)


classifier = load_model()


def predict_ticket(subcategory: str, description: str):
    text = f"{subcategory} {description}"

    probabilities = classifier.predict_proba([text])[0]
    classes = classifier.classes_
    best_index = probabilities.argmax()

    prediction = classes[best_index]
    confidence = probabilities[best_index]

    return str(prediction), float(confidence)