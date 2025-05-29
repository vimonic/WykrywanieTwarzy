import os
import cv2
import time
import numpy as np
import sys
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap
from ui.ui_add_employee import Ui_AddEmployeeWindow
from models.train_model import train_model

EMPLOYEES_DIR = "employees"

class VideoCaptureThread(QThread):
    update_frame = pyqtSignal(np.ndarray)

    def __init__(self, cap):
        super().__init__()
        self.cap = cap
        self.running = True

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.update_frame.emit(frame)

    def stop(self):
        self.running = False
        self.wait()

class AddEmployeeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_AddEmployeeWindow()
        self.ui.setupUi(self)

        self.ui.startButton.clicked.connect(self.start_capture)
        self.video_thread = None
        self.cap = None
        self.employee_name = ""
        self.photo_count = 0
        self.instructions = ["Patrz prosto", "Obróć głowę w lewo", "Obróć głowę w prawo", "Spójrz w górę", "Spójrz w dół"]
        self.current_instruction = 0

        self.ui.videoLabel = QLabel(self)
        self.ui.videoLabel.setGeometry(50, 100, 640, 480)
        self.ui.videoLabel.setStyleSheet("border: 1px solid black;")

    def start_capture(self):
        self.employee_name = self.ui.nameInput.text().strip()
        if not self.employee_name:
            QMessageBox.warning(self, "Błąd", "Podaj nazwę pracownika!")
            return

        self.save_path = os.path.join(EMPLOYEES_DIR, self.employee_name)
        os.makedirs(self.save_path, exist_ok=True)

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Błąd", "Nie udało się otworzyć kamery.")
            return

        self.video_thread = VideoCaptureThread(self.cap)
        self.video_thread.update_frame.connect(self.display_frame)
        self.video_thread.start()
        self.photo_count = 0
        self.current_instruction = 0
        self.capture_photos()

    def display_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format.Format_RGB888)
        self.ui.videoLabel.setPixmap(QPixmap.fromImage(image))

    def capture_photos(self):
        if self.photo_count < 100:
            ret, frame = self.cap.read()
            if ret:
                file_path = os.path.join(self.save_path, f"{self.photo_count}.jpg")
                cv2.imwrite(file_path, frame)
                self.photo_count += 1

                if self.photo_count % 20 == 0 and self.current_instruction < len(self.instructions) - 1:
                    self.current_instruction += 1
                    QMessageBox.information(self, "Instrukcja", self.instructions[self.current_instruction])

            QTimer.singleShot(500, self.capture_photos)  # Kontynuuj cykl zdjęć
        else:
            # Dopiero teraz zatrzymaj kamerę i rozpocznij trening
            self.video_thread.stop()
            self.cap.release()
            QMessageBox.information(self, "Sukces", "Zdjęcia zapisane. Rozpoczynam trening modelu...")
            train_model()
            QMessageBox.information(self, "Sukces", "Trening zakończony!")

    def closeEvent(self, event):
        if self.video_thread:
            self.video_thread.stop()
        if self.cap and self.cap.isOpened():
            self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AddEmployeeWindow()
    window.show()
    sys.exit(app.exec())