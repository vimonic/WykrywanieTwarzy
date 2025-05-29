import cv2
import numpy as np
from datetime import datetime
import csv
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QGridLayout, QMessageBox,
    QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QFont
from database.models import UserModel

class AccessLogsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.user_model = UserModel()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Tytuł
        title = QLabel("Historia Logowań")
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

        # Panel przycisków
        button_layout = QHBoxLayout()

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
        button_layout.addWidget(refresh_btn)

        # Przycisk eksportu do CSV
        export_btn = QPushButton("Eksportuj do CSV")
        export_btn.clicked.connect(self.export_to_csv)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(export_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.load_events()

    def load_events(self):
        # Wyczyść istniejące zdarzenia
        for i in reversed(range(self.events_layout.count())): 
            self.events_layout.itemAt(i).widget().setParent(None)

        # Pobierz zdarzenia z bazy danych
        events = self.user_model.get_access_logs()

        # Dodaj zdarzenia do interfejsu
        for row, (event_id, timestamp, user_id, username, status, image_bytes, confidence) in enumerate(events):
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

            if image_bytes:
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
            
            user_label = QLabel(f"Użytkownik: {username}")
            user_label.setStyleSheet("font-weight: bold; color: #2980b9;")
            info_layout.addWidget(user_label)
            
            if confidence is not None:
                confidence_label = QLabel(f"Pewność: {confidence * 100:.2f}%")
                confidence_label.setStyleSheet("font-weight: bold; color: #27ae60;")
                info_layout.addWidget(confidence_label)
            
            event_layout.addLayout(info_layout)
            event_layout.addStretch()
            
            event_frame.setLayout(event_layout)
            self.events_layout.addWidget(event_frame, row, 0)

        # Dodaj elastyczny element na końcu
        self.events_layout.addWidget(QWidget(), len(events), 0)
        self.events_layout.setRowStretch(len(events), 1)

    def export_to_csv(self):
        """Eksportuje historię logowań do pliku CSV"""
        # Pobierz dane do eksportu
        logs = self.user_model.get_access_logs()
        
        if not logs:
            QMessageBox.warning(
                self,
                "Brak danych",
                "Brak danych do wyeksportowania."
            )
            return

        # Wybierz lokalizację zapisu pliku
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz plik CSV",
            "",
            "Pliki CSV (*.csv)"
        )

        if file_path:
            # Dodaj rozszerzenie .csv jeśli nie zostało podane
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'

            try:
                # Utwórz folder na zdjęcia
                images_folder = os.path.join(os.path.dirname(file_path), "zdjecia_logow")
                os.makedirs(images_folder, exist_ok=True)

                # Zapisz do CSV
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    # Nagłówki
                    writer.writerow(['ID', 'Data i czas', 'ID użytkownika', 'Nazwa użytkownika', 
                                   'Status', 'Pewność', 'Ścieżka do zdjęcia'])

                    # Dane
                    for log in logs:
                        log_id, timestamp, user_id, username, status, image_bytes, confidence = log
                        
                        # Zapisz zdjęcie jeśli istnieje
                        image_path = ""
                        if image_bytes:
                            image_filename = f"log_{log_id}.jpg"
                            image_path = os.path.join("zdjecia_logow", image_filename)
                            full_image_path = os.path.join(images_folder, image_filename)
                            
                            # Konwertuj i zapisz zdjęcie
                            nparr = np.frombuffer(image_bytes, np.uint8)
                            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            cv2.imwrite(full_image_path, img)

                        # Formatuj pewność
                        if confidence is not None:
                            confidence_str = f"{float(confidence) * 100:.2f}%"
                        else:
                            confidence_str = "N/A"

                        # Zapisz wiersz
                        writer.writerow([log_id, timestamp, user_id, username, 
                                       status, confidence_str, image_path])

                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Dane zostały wyeksportowane do:\n{file_path}\n\nZdjęcia zostały zapisane w folderze:\n{images_folder}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Błąd",
                    f"Wystąpił błąd podczas eksportu danych:\n{str(e)}"
                ) 