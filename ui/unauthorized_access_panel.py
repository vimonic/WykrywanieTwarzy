import cv2
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QFont
from database.models import UserModel
import os
from notifications.notification_manager import notification_manager

class UnauthorizedAccessPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.user_model = UserModel()
        self.init_ui()
        self.unauthorized_attempts = []

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Tytuł
        title = QLabel("Nieuprawnione Próby Dostępu")
        title.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title.setStyleSheet('color: #333; margin-bottom: 20px;')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Obszar przewijania dla zdarzeń
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        # Kontener na zdarzenia
        self.events_container = QWidget()
        self.events_layout = QGridLayout()
        self.events_container.setLayout(self.events_layout)
        scroll_area.setWidget(self.events_container)

        layout.addWidget(scroll_area)

        # Przycisk odświeżania
        refresh_btn = QPushButton("Odśwież")
        refresh_btn.clicked.connect(self.load_events)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(refresh_btn)

        self.setLayout(layout)
        self.load_events()

    def load_events(self):
        # Wyczyść istniejące zdarzenia
        for i in reversed(range(self.events_layout.count())): 
            self.events_layout.itemAt(i).widget().setParent(None)

        # Pobierz zdarzenia z bazy danych
        events = self.user_model.get_unauthorized_attempts()

        # Dodaj zdarzenia do interfejsu
        for row, (event_id, timestamp, image_bytes, confidence) in enumerate(events):
            # Kontener na pojedyncze zdarzenie
            event_frame = QFrame()
            event_frame.setStyleSheet("""
                QFrame {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: white;
                    margin: 5px;
                    padding: 10px;
                }
            """)
            event_layout = QHBoxLayout()

            # Konwertuj timestamp na czytelny format
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")

            # Konwertuj obraz z BLOB na QPixmap
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            h, w = img.shape[:2]
            
            # Przeskaluj obraz, zachowując proporcje
            target_height = 120
            aspect_ratio = w / h
            target_width = int(target_height * aspect_ratio)
            
            img = cv2.resize(img, (target_width, target_height))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = img.shape
            qt_img = QImage(img.data, w, h, ch * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_img)

            # Dodaj obraz
            img_label = QLabel()
            img_label.setPixmap(pixmap)
            img_label.setFixedSize(target_width, target_height)
            event_layout.addWidget(img_label)

            # Informacje o zdarzeniu
            info_layout = QVBoxLayout()
            
            time_label = QLabel(f"Data i czas: {formatted_time}")
            time_label.setStyleSheet("font-weight: bold;")
            info_layout.addWidget(time_label)
            
            # Handle confidence value that might be bytes
            try:
                if isinstance(confidence, bytes):
                    confidence = float(confidence.decode())
                elif isinstance(confidence, str):
                    confidence = float(confidence)
                else:
                    confidence = float(confidence)
            except (ValueError, UnicodeDecodeError, TypeError):
                confidence = 0.0
                
            confidence_label = QLabel(f"Pewność: {confidence * 100:.2f}%")
            confidence_label.setStyleSheet("""
                font-weight: bold;
                color: #e74c3c;
            """)
            info_layout.addWidget(confidence_label)
            
            # Przycisk usuwania
            delete_btn = QPushButton("Usuń")
            delete_btn.setFixedSize(60, 25)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            delete_btn.clicked.connect(lambda checked, eid=event_id: self.delete_attempt(eid))
            info_layout.addWidget(delete_btn)
            
            event_layout.addLayout(info_layout)
            event_layout.addStretch()
            
            event_frame.setLayout(event_layout)
            self.events_layout.addWidget(event_frame, row, 0)

        # Dodaj elastyczny element na końcu
        self.events_layout.addWidget(QWidget(), len(events), 0)
        self.events_layout.setRowStretch(len(events), 1)

    def delete_attempt(self, attempt_id):
        """Usuwa próbę nieautoryzowanego dostępu"""
        reply = QMessageBox.question(
            self,
            'Potwierdzenie',
            'Czy na pewno chcesz usunąć tę próbę dostępu?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.user_model.delete_unauthorized_attempt(attempt_id):
                self.load_events()  # Odśwież listę
            else:
                QMessageBox.warning(
                    self,
                    'Błąd',
                    'Nie udało się usunąć próby dostępu.'
                )

    def add_unauthorized_attempt(self, image_path, confidence_score):
        """Dodaje nową próbę nieautoryzowanego dostępu i wysyła powiadomienie"""
        current_time = datetime.now()
        
        # Wysyłanie powiadomienia email
        notification_sent = notification_manager.send_unauthorized_access_notification(
            image_path,
            confidence_score
        )
        
        # Dodawanie do listy prób
        self.unauthorized_attempts.append({
            'timestamp': current_time,
            'image_path': image_path,
            'confidence': confidence_score,
            'notification_sent': notification_sent
        })
        
        # Odśwież listę zdarzeń
        self.load_events() 