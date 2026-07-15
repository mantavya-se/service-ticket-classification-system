import joblib
from pathlib import Path

MODEL_PATH = Path("models/ticket_classifier_split_v1.joblib")

classifier = joblib.load(MODEL_PATH)
text = input("Ticket Subcategory + Description: ")

probabilities = classifier.predict_proba([text])[0]
classes = classifier.classes_
best_index = probabilities.argmax()

prediction = classifier.predict([text])
confidence = probabilities[best_index]

print(f"Category: {prediction}")
print(f"Confidence rating: {confidence:.2%}")