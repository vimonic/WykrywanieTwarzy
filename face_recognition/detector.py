import cv2
from pathlib import Path

import cv2
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

class FaceDetector:
    def __init__(self):
        self.detector = cv2.CascadeClassifier(CASCADE_PATH)

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        # Zwraca listę ROI (x, y, w, h)
        return faces