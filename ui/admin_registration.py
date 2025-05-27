import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QPushButton, QLabel,
    QVBoxLayout, QWidget, QHBoxLayout, QMessageBox, QInputDialog
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QFont, QPainter, QPen

from face_recognition.detector import FaceDetector
from face_recognition.embedder import FaceEmbedder
from database.models import UserModel
from utils.image_utils import preprocess_face


class AdminRegistration(QMainWindow):
    # Sygnał emitowany po zakończeniu rejestracji
    registration_complete = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Face Access - Rejestracja Admina')
        self.resize(900, 700)
        self.setStyleSheet('background-color: #f0f2f5;')

        # Face recognition modules
        self.detector = FaceDetector()
        self.embedder = FaceEmbedder()
        self.user_model = UserModel()
        self.desired_reg_count = 3

        # UI elements
        title = QLabel('Rejestracja Admina')
        title.setFont(QFont('Segoe UI', 20, QFont.Bold))
        title.setStyleSheet('color: #333; padding: 15px;')

        back_btn = QPushButton('Anuluj')
        exit_btn = QPushButton('Wyjście')
        for btn in (back_btn, exit_btn):
            btn.setFont(QFont('Segoe UI', 10))
            btn.setFixedSize(80, 30)
            btn.setStyleSheet(
                'QPushButton { background-color: #73198a; color: white; border: none; border-radius: 5px; }'
                'QPushButton:hover { background-color: #451552; }'
                'QPushButton:pressed { background-color: #662378; }'
            )
        back_btn.clicked.connect(self.cancel_registration)
        exit_btn.clicked.connect(self.close)

        top_layout = QHBoxLayout()
        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(back_btn)
        top_layout.addWidget(exit_btn)

        # Video display
        self.video_label = QLabel()
        self.video_label.setFixedSize(800, 450)
        self.video_label.setStyleSheet('border: 2px solid #ccc; border-radius: 8px; background-color: #000;')
        self.video_label.setAlignment(Qt.AlignCenter)
        self.placeholder = self.generate_placeholder(800, 450)
        self.video_label.setPixmap(self.placeholder)

        # Status label
        self.status_label = QLabel('Podaj nazwę administratora i rozpocznij rejestrację')
        self.status_label.setFont(QFont('Segoe UI', 14))
        self.status_label.setAlignment(Qt.AlignCenter)

        # Buttons
        self.start_btn = QPushButton('Rozpocznij rejestrację')
        self.start_btn.setFont(QFont('Segoe UI', 14))
        self.start_btn.setFixedSize(250, 50)
        self.start_btn.setStyleSheet(
            'QPushButton { background-color: #09ab3c; color: white; border: none; border-radius: 8px; }'
            'QPushButton:hover { background-color: #0e4a21; }'
            'QPushButton:pressed { background-color: #158a3a; }'
        )
        self.start_btn.clicked.connect(self.start_registration)

        self.capture_btn = QPushButton('Zapisz próbkę')
        self.capture_btn.setFont(QFont('Segoe UI', 14))
        self.capture_btn.setFixedSize(200, 50)
        self.capture_btn.setStyleSheet(
            'QPushButton { background-color: #007ACC; color: white; border: none; border-radius: 8px; }'
            'QPushButton:hover { background-color: #005f99; }'
            'QPushButton:pressed { background-color: #004f80; }'
        )
        self.capture_btn.clicked.connect(self.trigger_capture)
        self.capture_btn.hide()

        # Layouts
        video_layout = QHBoxLayout()
        video_layout.addStretch()
        video_layout.addWidget(self.video_label)
        video_layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.capture_btn)
        btn_layout.addStretch()

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(video_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addSpacing(20)
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Timer and flags
        self.capture = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.ready_to_capture = False
        self.registration_mode = False
        self.reg_user_id = None
        self.reg_count = 0
        self.new_user_name = None

    def generate_placeholder(self, width: int, height: int) -> QPixmap:
        pix = QPixmap(width, height)
        pix.fill(Qt.black)
        painter = QPainter(pix)
        pen = QPen(Qt.white, 4)
        painter.setPen(pen)
        head_w, head_h = int(width * 0.4), int(height * 0.8)
        head_x, head_y = (width - head_w) // 2, int(height * 0.1)
        painter.drawEllipse(head_x, head_y, head_w, head_h)
        eye_w, eye_h = int(head_w * 0.1), int(head_h * 0.1)
        eye_y = head_y + int(head_h * 0.35)
        painter.drawEllipse(head_x + int(head_w * 0.25), eye_y, eye_w, eye_h)
        painter.drawEllipse(head_x + int(head_w * 0.65), eye_y, eye_w, eye_h)
        mouth_y = head_y + int(head_h * 0.7)
        painter.drawLine(head_x + int(head_w * 0.3), mouth_y, head_x + int(head_w * 0.7), mouth_y)
        painter.end()
        return pix

    def start_registration(self):
        text, ok = QInputDialog.getText(self, "Rejestracja Admina",
                                        "Podaj nazwę użytkownika (np. Admin1):")
        if not ok or not text:
            return
        self.new_user_name = text
        self.registration_mode = True
        self.reg_user_id = None
        self.reg_count = 0
        self.start_camera()
        self.capture_btn.show()
        self.start_btn.hide()
        self.status_label.setText(
            f"Rejestracja użytkownika: {self.new_user_name}. Zbierz {self.desired_reg_count} próbek.")

    def start_camera(self):
        if self.capture is None:
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                QMessageBox.warning(self, "Błąd kamery", "Nie można otworzyć kamery")
                self.capture = None
                return
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 450)
            self.timer.start(30)

    def stop_camera(self):
        if self.capture is not None:
            self.timer.stop()
            self.capture.release()
            self.capture = None
            self.video_label.setPixmap(self.placeholder)
            self.registration_mode = False
            self.ready_to_capture = False

    def trigger_capture(self):
        self.ready_to_capture = True

    def cancel_registration(self):
        self.stop_camera()
        self.close()
        self.registration_complete.emit()

    def update_frame(self):
        if self.capture is None:
            return
        ret, frame = self.capture.read()
        if not ret:
            return

        faces = self.detector.detect_faces(frame)

        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_img = frame[y:y + h, x:x + w]

            # Oznacz wykrytą twarz
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Rejestracja - zbieramy N próbek
            if self.registration_mode and self.ready_to_capture:
                proc = preprocess_face(face_img)
                emb = self.embedder.get_embedding(proc)

                # Pierwsza próbka tworzy nowego użytkownika
                if not self.reg_user_id:
                    self.reg_user_id = self.user_model.add_user(
                        self.new_user_name, emb, role='ADMIN'
                    )
                else:
                    # Kolejne próbki dopisujemy do istniejącego user_id
                    self.user_model.add_embedding(self.reg_user_id, emb)

                # Inkrementacja licznika i reset flagi
                self.reg_count += 1
                self.ready_to_capture = False
                self.status_label.setText(f"Zarejestrowano próbkę {self.reg_count}/{self.desired_reg_count}")
                print(f"Zarejestrowano próbkę {self.reg_count}/{self.desired_reg_count}")

                # Jeżeli mamy już dostatecznie dużo próbek — zakończ rejestrację
                if self.reg_count >= self.desired_reg_count:
                    self.stop_camera()
                    QMessageBox.information(
                        self, "Rejestracja zakończona",
                        f"Zarejestrowano {self.reg_count} próbek dla użytkownika {self.new_user_name}."
                    )
                    self.close()
                    self.registration_complete.emit()

        # Convert to QImage and display
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AdminRegistration()
    window.show()
    sys.exit(app.exec_())