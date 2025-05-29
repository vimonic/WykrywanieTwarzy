import cv2
import numpy as np

def preprocess_face(face_img, size=(160, 160)):
    # 1) Konwersja BGR → RGB
    face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    # 2) Resize do 160×160
    face = cv2.resize(face, size)
    # 3) Żadnej normalizacji na poziomie pikseli – zostawiamy uint8
    return np.expand_dims(face, axis=0)  # shape = (1,160,160,3), dtype=uint8