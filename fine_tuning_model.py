# skrypt do wczytania poprzedniego modelu i kontynuowania trenowania
import os
import cv2
import numpy as np
import pickle
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

def load_data(data_dir, img_size=(100, 100)):
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    images, labels = [], []

    for label in os.listdir(data_dir):
        folder = os.path.join(data_dir, label)
        if not os.path.isdir(folder):
            continue
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            img = cv2.imread(file_path)
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            if len(faces) == 0:
                continue
            (x, y, w, h) = faces[0]
            face_resized = cv2.resize(gray[y:y + h, x:x + w], img_size)
            face_normalized = face_resized.astype('float32') / 255.0
            face_normalized = np.expand_dims(face_normalized, axis=-1)
            images.append(face_normalized)
            labels.append(label)
    return np.array(images), np.array(labels)

def print_versions():
    print(f"TensorFlow version: {tf.__version__}")
    import sklearn
    print(f"scikit-learn version: {sklearn.__version__}")
    import cv2
    print(f"OpenCV version: {cv2.__version__}")
    import numpy as np
    print(f"NumPy version: {np.__version__}")
    gpus = tf.config.list_physical_devices('GPU')
    print("GPU available:" if gpus else "No GPU available.")

if __name__ == '__main__':
    print_versions()

    data_dir = './data'
    print("Loading data...")
    X, y = load_data(data_dir)
    print(f"Loaded {len(X)} images.")

    if len(X) == 0:
        print("Brak danych! Sprawdź strukturę folderu 'data'.")
        exit()

    with open('label_encoder.pkl', 'rb') as f:
        le = pickle.load(f)
    y_encoded = le.transform(y)
    y_categorical = to_categorical(y_encoded)

    X_train, X_val, y_train, y_val = train_test_split(X, y_categorical, test_size=0.2, random_state=42)

    print("Loading existing model...")
    model = load_model("final_model.h5") # nazwa wczytywanego modelu
    model.summary()

    checkpoint = ModelCheckpoint('model_finetuned_checkpoint.h5', monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')
    callbacks_list = [checkpoint]

    print("Fine-tuning model...")
    history = model.fit(X_train, y_train, epochs=5, batch_size=32, validation_data=(X_val, y_val), callbacks=callbacks_list)

    model.save("final_model_finetuned.h5") #nazwa nowego ulepszonego modelu
    print("Fine-tuning complete. Model saved as final_model_finetuned.h5.")