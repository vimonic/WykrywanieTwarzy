import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import os

MODEL_PATH = "models/trained_model.h5"
LABELS_PATH = "models/label_encoder.npy"

if not os.path.exists(MODEL_PATH) or not os.path.exists(LABELS_PATH):
    print("Brak modelu lub etykiet! Najpierw przetrenuj model.")
    exit()

model = load_model(MODEL_PATH)
labels = np.load(LABELS_PATH, allow_pickle=True)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def start_recognition():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Błąd: Nie można uruchomić kamery!")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(50, 50))

        for (x, y, w, h) in faces:
            face = cv2.resize(frame[y:y + h, x:x + w], (100, 100))
            face = np.expand_dims(img_to_array(face) / 255.0, axis=0)

            prediction = model.predict(face)
            label = np.argmax(prediction)
            confidence = prediction.max()

            text = f"Przyznano dostep: {labels[label]}" if confidence > 0.7 else "Dostep zabroniony!"
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0) if confidence > 0.7 else (0, 0, 255), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0) if confidence > 0.7 else (0, 0, 255), 2)

        cv2.imshow("Podgląd kamery", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
