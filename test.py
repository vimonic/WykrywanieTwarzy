import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import pickle

# Załaduj wytrenowany model
model = load_model('final_model_v1.h5')

# Załaduj zapisany obiekt LabelEncoder (upewnij się, że został zapisany podczas treningu)
with open('label_encoder.pkl', 'rb') as f:
    le = pickle.load(f)

# Utwórz słownik mapujący indeksy na etykiety
label_dict = {i: label for i, label in enumerate(le.classes_)}

# Wczytaj kaskadę Haar do wykrywania twarzy
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(cascade_path)

# Inicjalizacja kamery
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Nie udało się otworzyć kamery")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Nie udało się pobrać obrazu z kamery")
        break

    # Konwersja obrazu do skali szarości
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Wykrywanie twarzy
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    for (x, y, w, h) in faces:
        # Wytnij i przygotuj obraz twarzy
        face = gray[y:y + h, x:x + w]
        face_resized = cv2.resize(face, (100, 100))  # upewnij się, że rozmiar pasuje do wejścia modelu
        face_normalized = face_resized.astype('float32') / 255.0
        # Dodaj wymiar kanału, jeśli model oczekuje (100, 100, 1)
        face_normalized = np.expand_dims(face_normalized, axis=-1)
        # Rozszerz wymiary, by utworzyć batch o rozmiarze 1
        face_input = np.expand_dims(face_normalized, axis=0)

        # Przewidywanie etykiety
        preds = model.predict(face_input)
        pred_idx = np.argmax(preds, axis=1)[0]
        predicted_label = label_dict.get(pred_idx, "Nieznany")

        # Rysowanie prostokąta i etykiety na obrazie
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, predicted_label, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

    # Wyświetlanie obrazu z kamery
    cv2.imshow('Rozpoznawanie Twarzy', frame)

    # Naciśnij 'q', aby zakończyć
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()