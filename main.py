import os
import cv2
import numpy as np
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.callbacks import ModelCheckpoint
import tensorflow as tf
import pickle

from tensorflow.keras.models import load_model


def load_data(data_dir, img_size=(100, 100)):
    # Inicjalizacja detektora twarzy
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    images = []
    labels = []

    # Iteracja po folderach w katalogu data
    for label in os.listdir(data_dir):
        folder = os.path.join(data_dir, label)
        if not os.path.isdir(folder):
            continue
        # Iteracja po plikach w folderze danej osoby
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            img = cv2.imread(file_path)
            if img is None:
                continue
            # Konwersja na skalę szarości (można pozostawić kolor, ale wtedy zmień input_shape w modelu)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Wykrywanie twarzy
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            if len(faces) == 0:
                continue
            # Przyjmujemy pierwszą wykrytą twarz
            (x, y, w, h) = faces[0]
            face = gray[y:y + h, x:x + w]
            # Zmiana rozmiaru do ustalonego formatu
            face_resized = cv2.resize(face, img_size)
            # Normalizacja pikseli do zakresu [0,1]
            face_normalized = face_resized.astype('float32') / 255.0
            # Dodanie wymiaru kanału (bo obraz jest szary)
            face_normalized = np.expand_dims(face_normalized, axis=-1)
            images.append(face_normalized)
            labels.append(label)
    return np.array(images), np.array(labels)


def build_model(input_shape, num_classes):
    model = Sequential([
        Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
        MaxPooling2D((2, 2)),
        Conv2D(64, (3, 3), activation='relu'),
        MaxPooling2D((2, 2)),
        Flatten(),
        Dense(128, activation='relu'),
        Dropout(0.5),
        Dense(num_classes, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model


def print_versions():
    print(f"TensorFlow version: {tf.__version__}")
    import sklearn
    print(f"scikit-learn version: {sklearn.__version__}")
    import cv2
    print(f"OpenCV version: {cv2.__version__}")
    import numpy as np
    print(f"NumPy version: {np.__version__}")
    # Sprawdzenie dostępności GPU
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        print("GPU is available:")
        for gpu in gpus:
            print(gpu)
    else:
        print("No GPU available.")


if __name__ == '__main__':
    # Wypisanie wersji pakietów oraz dostępności GPU
    print_versions()

    # Załaduj dane z folderu ./data
    data_dir = './data'
    print("Loading data...")
    X, y = load_data(data_dir)
    print(f"Loaded {len(X)} images.")

    if len(X) == 0:
        print("Brak danych! Sprawdź strukturę folderu 'data'.")
        exit()

    # Kodowanie etykiet
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    y_categorical = to_categorical(y_encoded)

    # Zapisanie obiektu LabelEncoder do pliku
    with open('label_encoder.pkl', 'wb') as f:
        pickle.dump(le, f)
    print("Label encoder saved as 'label_encoder.pkl'.")

    # Podział danych na zbiór treningowy i walidacyjny
    X_train, X_val, y_train, y_val = train_test_split(X, y_categorical, test_size=0.2, random_state=42)

    # Budowa modelu
    print("Building model...")
    input_shape = X_train.shape[1:]  # np. (100, 100, 1)
    num_classes = y_categorical.shape[1]
    model = build_model(input_shape, num_classes)
    model.summary()

    # Callback do zapisywania najlepszych wag (na podstawie accuracy na zbiorze walidacyjnym)
    checkpoint = ModelCheckpoint('model_checkpoint.h5', monitor='val_accuracy', verbose=1,
                                 save_best_only=True, mode='max')
    callbacks_list = [checkpoint]

    # Trenowanie modelu
    print("Training model...")
    history = model.fit(X_train, y_train, epochs=10, batch_size=32,
                        validation_data=(X_val, y_val), callbacks=callbacks_list)

    # Zapisanie finalnego modelu
    model.save("final_model_v1.h5")
    print("Training complete. Model saved as final_model.h5.")