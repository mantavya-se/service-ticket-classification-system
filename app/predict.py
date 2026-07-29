import joblib
from pathlib import Path
from infrastructure.s3_storage import download_file

# BASE_DIR = Path(__file__).resolve().parent.parent
# MODEL_PATH = BASE_DIR / "models" / "ticket_classifier_split_v1.joblib"

MODEL_BUCKET = os.environ["MODEL_S3_BUCKET"]
MODEL_KEY = os.environ["MODEL_S3_KEY"]
MODEL_AWS_PATH = Path(os.getenv("MODEL_AWS_PATH", "/tmp/ticket-classifier.joblib"))

def load_model():
    download_file(
        bucket = MODEL_BUCKET,
        key = MODEL_KEY,
        local_path = MODEL_AWS_PATH
    )
    return joblib.load(MODEL_AWS_PATH)

classifier = load_model()
# classifier = joblib.load(MODEL_PATH)

def predict_ticket(subcategory:str, description: str):
    text  = f"{subcategory} {description}"

    probabilities = classifier.predict_proba([text])[0]
    classes = classifier.classes_
    best_index = probabilities.argmax()

    prediction = classifier.predict([text])
    confidence = probabilities[best_index]

    return str(prediction), float(confidence)