import cv2
from pathlib import Path

import cv2
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

class FaceDetector:
    def __init__(self):
        self.detector = cv2.CascadeClassifier(CASCADE_PATH)
        self.current_frame = None

    def detect_faces(self, frame):
        self.current_frame = frame  # Store the current frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        return faces

    def get_current_frame(self):
        """Returns the current frame and success flag"""
        if self.current_frame is None:
            return False, None
        return True, self.current_frame.copy()