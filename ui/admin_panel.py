import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QInputDialog, QMessageBox, QDialog, QComboBox, QLineEdit, QDialogButtonBox,
    QTableWidget, QHeaderView, QTableWidgetItem, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QImage, QPixmap, QPainter, QPen

from face_recognition.detector import FaceDetector
from face_recognition.embedder import FaceEmbedder
from database.models import UserModel
from utils.image_utils import preprocess_face
from ui.metrics_window import MetricsWindow

class UserEditDialog(QDialog):
    """Dialog for editing user information"""

    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data  # (id, name, role, embedding_count)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Edytuj użytkownika")
        self.setModal(True)
        self.setFixedSize(350, 200)

        layout = QFormLayout()

        # Name input
        self.name_input = QLineEdit()
        self.name_input.setText(self.user_data[1])  # Current name
        self.name_input.setFont(QFont('Segoe UI', 11))
        layout.addRow("Nazwa użytkownika:", self.name_input)

        # Role selection
        self.role_combo = QComboBox()
        self.role_combo.addItems(['USER', 'ADMIN'])
        self.role_combo.setCurrentText(self.user_data[2])  # Current role
        self.role_combo.setFont(QFont('Segoe UI', 11))
        layout.addRow("Rola:", self.role_combo)

        # Info label
        info_label = QLabel(f"ID: {self.user_data[0]} | Próbki: {self.user_data[3]}")
        info_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addRow(info_label)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Style buttons
        button_box.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton[text="OK"] {
                background-color: #09ab3c;
                color: white;
            }
            QPushButton[text="OK"]:hover {
                background-color: #078a30;
            }
            QPushButton[text="Cancel"] {
                background-color: #e74c3c;
                color: white;
            }
            QPushButton[text="Cancel"]:hover {
                background-color: #c0392b;
            }
        """)

        layout.addRow(button_box)
        self.setLayout(layout)

    def get_data(self):
        """Return the edited data"""
        return {
            'name': self.name_input.text().strip(),
            'role': self.role_combo.currentText()
        }

class AdminPanel(QWidget):
    """Panel shown to administrators after successful authentication"""

    logout_requested = pyqtSignal()  # Signal to notify logout request

    def __init__(self, username="Admin"):
        super().__init__()
        self.username = username
        self.user_model = UserModel()

        # Face recognition modules for user registration
        self.detector = FaceDetector()
        self.embedder = FaceEmbedder()
        self.desired_reg_count = 3

        # Registration state
        self.capture = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.registration_mode = False
        self.ready_to_capture = False
        self.reg_user_id = None
        self.reg_count = 0
        self.new_user_name = None

        self.init_ui()

    def init_ui(self):
        """Initialize the admin panel UI"""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Welcome header
        welcome_label = QLabel(f"Witaj, {self.username}")
        welcome_label.setFont(QFont('Segoe UI', 24, QFont.Bold))
        welcome_label.setStyleSheet('color: #333;')
        welcome_label.setAlignment(Qt.AlignCenter)

        # Admin info label
        info_label = QLabel("Panel administratora")
        info_label.setFont(QFont('Segoe UI', 12))
        info_label.setStyleSheet('color: #666;')
        info_label.setAlignment(Qt.AlignCenter)

        # Create menu buttons
        add_user_btn = self.create_menu_button('Dodaj użytkownika')
        add_user_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        user_list_btn = self.create_menu_button('Lista użytkowników')
        user_list_btn.clicked.connect(lambda: self.show_user_list())

        # metrics_btn  = self.create_menu_button('Metryki systemu')
        # self.metrics_btn.clicked.connect(self.show_metrics_window)
        metrics_btn = self.create_menu_button('Metryki systemu')
        metrics_btn.clicked.connect(self.show_metrics_window)

        settings_btn = self.create_menu_button('Ustawienia aplikacji')
        settings_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        logout_btn = self.create_menu_button('Wyloguj się')
        logout_btn.setStyleSheet(
            'QPushButton { background-color: #73198a; color: white; '
            'border: none; border-radius: 5px; }'
            'QPushButton:hover { background-color: #451552; }'
            'QPushButton:pressed { background-color: #662378; }'
        )
        logout_btn.clicked.connect(self.on_logout)

        # Menu layout
        menu_layout = QHBoxLayout()
        menu_layout.addWidget(add_user_btn)
        menu_layout.addWidget(user_list_btn)
        menu_layout.addWidget(metrics_btn)
        menu_layout.addWidget(settings_btn)
        menu_layout.addWidget(logout_btn)

        # Create content area
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_user_registration_panel())
        self.stack.addWidget(self.create_user_list_panel())
        self.stack.addWidget(self.create_placeholder_panel("Ustawienia aplikacji",
                                                           "Ta funkcjonalność zostanie zaimplementowana wkrótce."))

        # Content frame with styling
        content_frame = QFrame()
        content_frame.setStyleSheet('background-color: #f8f8f8; border-radius: 8px; border: 1px solid #ddd;')
        content_layout = QVBoxLayout(content_frame)
        content_layout.addWidget(self.stack)

        # Add all elements to main layout
        main_layout.addWidget(welcome_label)
        main_layout.addWidget(info_label)
        main_layout.addSpacing(15)
        main_layout.addLayout(menu_layout)
        main_layout.addSpacing(10)
        main_layout.addWidget(content_frame)

        self.setLayout(main_layout)

    def create_menu_button(self, text):
        """Create a menu button with consistent styling"""
        btn = QPushButton(text)
        btn.setFont(QFont('Segoe UI', 12))
        btn.setFixedHeight(40)
        btn.setStyleSheet(
            'QPushButton { background-color: #09ab3c; color: white; '
            'border: none; border-radius: 5px; }'
            'QPushButton:hover { background-color: #078a30; }'
            'QPushButton:pressed { background-color: #067025; }'
        )
        return btn

    def create_placeholder_panel(self, title, message):
        """Create a placeholder panel for features to be implemented later"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title)
        title_label.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title_label.setStyleSheet('color: #333;')
        title_label.setAlignment(Qt.AlignCenter)

        msg_label = QLabel(message)
        msg_label.setFont(QFont('Segoe UI', 12))
        msg_label.setStyleSheet('color: #666;')
        msg_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(msg_label)
        panel.setLayout(layout)
        return panel

    def create_user_list_panel(self):
        """Create the user list panel"""
        panel = QWidget()
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Lista użytkowników")
        title_label.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title_label.setStyleSheet('color: #333;')
        title_label.setAlignment(Qt.AlignCenter)

        # Refresh button
        refresh_btn = QPushButton("Odśwież")
        refresh_btn.setFixedSize(100, 30)
        refresh_btn.clicked.connect(self.refresh_user_list)
        refresh_btn.setStyleSheet(
            'QPushButton { background-color: #007ACC; color: white; border: none; border-radius: 5px; }'
            'QPushButton:hover { background-color: #005f99; }'
        )

        # Table
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels(['ID', 'Nazwa', 'Rola', 'Próbki', 'Akcje'])

        # Set column widths
        header = self.user_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.resizeSection(4, 200)  # Fixed width for action buttons

        # Style the table
        self.user_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #ddd;
                font-weight: bold;
            }
        """)

        # Layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)

        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addLayout(btn_layout)
        layout.addWidget(self.user_table)

        panel.setLayout(layout)
        return panel

    def show_user_list(self):
        """Show user list and refresh data"""
        self.stack.setCurrentIndex(1)
        self.refresh_user_list()

    def refresh_user_list(self):
        """Refresh the user list table with current data"""
        try:
            users = self.user_model.get_all_users()
            self.user_table.setRowCount(len(users))
            self.user_table.verticalHeader().setDefaultSectionSize(60)

            for row, user_data in enumerate(users):
                user_id, name, role, embedding_count = user_data

                # Add user data to table
                self.user_table.setItem(row, 0, QTableWidgetItem(str(user_id)))
                self.user_table.setItem(row, 1, QTableWidgetItem(name))
                self.user_table.setItem(row, 2, QTableWidgetItem(role))
                self.user_table.setItem(row, 3, QTableWidgetItem(str(embedding_count)))

                # Create action buttons widget
                action_widget = QWidget()
                action_widget.setAttribute(Qt.WA_TranslucentBackground)
                action_widget.setStyleSheet("background: transparent; border: none;")
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 5, 5, 5)
                action_layout.setSpacing(5)

                # Edit button
                edit_btn = QPushButton("Edytuj")
                edit_btn.setFixedSize(60, 25)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f39c12;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #e67e22;
                    }
                """)
                edit_btn.clicked.connect(lambda checked, uid=user_id, data=user_data: self.edit_user(uid, data))

                # Delete button
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
                delete_btn.clicked.connect(lambda checked, uid=user_id, name=name: self.delete_user(uid, name))

                action_layout.addWidget(edit_btn)
                action_layout.addWidget(delete_btn)
                action_layout.addStretch()

                self.user_table.setCellWidget(row, 4, action_widget)

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można załadować listy użytkowników: {str(e)}")

    def show_metrics_window(self):
        """Show the metrics visualization window"""
        if not hasattr(self, 'metrics_window') or self.metrics_window is None:
            self.metrics_window = MetricsWindow(self)

        self.metrics_window.show()
        self.metrics_window.raise_()
        self.metrics_window.activateWindow()

    def edit_user(self, user_id, user_data):
        """Open edit dialog for user"""
        dialog = UserEditDialog(user_data, self)

        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()

            # Validate input
            if not new_data['name']:
                QMessageBox.warning(self, "Błąd", "Nazwa użytkownika nie może być pusta.")
                return

            # Update user in database
            try:
                success = self.user_model.update_user(
                    user_id,
                    name=new_data['name'],
                    role=new_data['role']
                )

                if success:
                    QMessageBox.information(self, "Sukces", "Dane użytkownika zostały zaktualizowane.")
                    self.refresh_user_list()  # Refresh the table
                else:
                    QMessageBox.warning(self, "Błąd", "Nie udało się zaktualizować danych użytkownika.")

            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Błąd podczas aktualizacji: {str(e)}")

    def delete_user(self, user_id, user_name):
        """Delete user with confirmation"""
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Potwierdzenie usunięcia",
            f"Czy na pewno chcesz usunąć użytkownika '{user_name}' (ID: {user_id})?\n\n"
            "Ta operacja jest nieodwracalna i usunie wszystkie dane użytkownika "
            "włącznie z próbkami twarzy.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success = self.user_model.delete_user(user_id)

                if success:
                    QMessageBox.information(self, "Sukces", f"Użytkownik '{user_name}' został usunięty.")
                    self.refresh_user_list()  # Refresh the table
                else:
                    QMessageBox.warning(self, "Błąd", "Nie udało się usunąć użytkownika.")

            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Błąd podczas usuwania: {str(e)}")

    def create_user_registration_panel(self):
        """Create the user registration panel"""
        panel = QWidget()
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Dodawanie użytkownika")
        title_label.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title_label.setStyleSheet('color: #333;')
        title_label.setAlignment(Qt.AlignCenter)

        # Video display
        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 360)  # Smaller size for admin panel
        self.video_label.setStyleSheet('border: 2px solid #ccc; border-radius: 8px; background-color: #000;')
        self.video_label.setAlignment(Qt.AlignCenter)
        self.placeholder = self.generate_placeholder(640, 360)
        self.video_label.setPixmap(self.placeholder)

        # Status label
        self.status_label = QLabel('Kliknij "Rozpocznij rejestrację" aby dodać nowego użytkownika')
        self.status_label.setFont(QFont('Segoe UI', 12))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet('color: #666;')

        # Buttons
        self.start_reg_btn = QPushButton('Rozpocznij rejestrację')
        self.start_reg_btn.setFont(QFont('Segoe UI', 12))
        self.start_reg_btn.setFixedSize(200, 40)
        self.start_reg_btn.setStyleSheet(
            'QPushButton { background-color: #09ab3c; color: white; border: none; border-radius: 8px; }'
            'QPushButton:hover { background-color: #0e4a21; }'
            'QPushButton:pressed { background-color: #158a3a; }'
        )
        self.start_reg_btn.clicked.connect(self.start_registration)

        self.capture_btn = QPushButton('Zapisz próbkę')
        self.capture_btn.setFont(QFont('Segoe UI', 12))
        self.capture_btn.setFixedSize(150, 40)
        self.capture_btn.setStyleSheet(
            'QPushButton { background-color: #007ACC; color: white; border: none; border-radius: 8px; }'
            'QPushButton:hover { background-color: #005f99; }'
            'QPushButton:pressed { background-color: #004f80; }'
        )
        self.capture_btn.clicked.connect(self.trigger_capture)
        self.capture_btn.hide()

        self.stop_reg_btn = QPushButton('Anuluj')
        self.stop_reg_btn.setFont(QFont('Segoe UI', 12))
        self.stop_reg_btn.setFixedSize(100, 40)
        self.stop_reg_btn.setStyleSheet(
            'QPushButton { background-color: #e74c3c; color: white; border: none; border-radius: 8px; }'
            'QPushButton:hover { background-color: #c0392b; }'
            'QPushButton:pressed { background-color: #a93226; }'
        )
        self.stop_reg_btn.clicked.connect(self.stop_registration)
        self.stop_reg_btn.hide()

        # Layouts
        video_layout = QHBoxLayout()
        video_layout.addStretch()
        video_layout.addWidget(self.video_label)
        video_layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_reg_btn)
        btn_layout.addWidget(self.capture_btn)
        btn_layout.addWidget(self.stop_reg_btn)
        btn_layout.addStretch()

        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addLayout(video_layout)
        layout.addWidget(self.status_label)
        layout.addSpacing(15)
        layout.addLayout(btn_layout)
        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def generate_placeholder(self, width: int, height: int) -> QPixmap:
        """Generate a face placeholder image"""
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
        """Start user registration process"""
        text, ok = QInputDialog.getText(self, "Rejestracja Użytkownika", "Podaj nazwę użytkownika:")
        if not ok or not text.strip():
            return

        self.new_user_name = text.strip()
        self.registration_mode = True
        self.reg_user_id = None
        self.reg_count = 0

        # Start camera
        if self.capture is None:
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                QMessageBox.warning(self, "Błąd kamery", "Nie można otworzyć kamery")
                self.capture = None
                self.registration_mode = False
                return
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
            self.timer.start(30)

        # Update UI
        self.start_reg_btn.hide()
        self.capture_btn.show()
        self.stop_reg_btn.show()
        self.status_label.setText(
            f"Rejestracja użytkownika: {self.new_user_name}. Zbierz {self.desired_reg_count} próbek twarzy.")

    def stop_registration(self):
        """Stop registration process"""
        if self.capture is not None:
            self.timer.stop()
            self.capture.release()
            self.capture = None
            self.video_label.setPixmap(self.placeholder)

        self.registration_mode = False
        self.ready_to_capture = False
        self.reg_user_id = None
        self.reg_count = 0

        # Update UI
        self.start_reg_btn.show()
        self.capture_btn.hide()
        self.stop_reg_btn.hide()
        self.status_label.setText('Kliknij "Rozpocznij rejestrację" aby dodać nowego użytkownika')

    def trigger_capture(self):
        """Trigger face capture"""
        self.ready_to_capture = True

    def update_frame(self):
        """Update camera frame"""
        if self.capture is None:
            return

        ret, frame = self.capture.read()
        if not ret:
            return

        faces = self.detector.detect_faces(frame)

        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_img = frame[y:y + h, x:x + w]

            # Draw rectangle around detected face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Registration mode - collect samples
            if self.registration_mode and self.ready_to_capture:
                proc = preprocess_face(face_img)
                emb = self.embedder.get_embedding(proc)

                # First sample creates new user with 'USER' role
                if not self.reg_user_id:
                    self.reg_user_id = self.user_model.add_user(
                        self.new_user_name, emb, role='USER'
                    )
                else:
                    # Subsequent samples are added to existing user
                    self.user_model.add_embedding(self.reg_user_id, emb)

                # Increment counter and reset flag
                self.reg_count += 1
                self.ready_to_capture = False
                self.status_label.setText(f"Zarejestrowano próbkę {self.reg_count}/{self.desired_reg_count}")

                # If we have enough samples, finish registration
                if self.reg_count >= self.desired_reg_count:
                    self.stop_registration()
                    QMessageBox.information(
                        self, "Rejestracja zakończona",
                        f"Pomyślnie zarejestrowano {self.reg_count} próbek dla użytkownika {self.new_user_name}."
                    )

        # Convert to QImage and display
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))

    def on_logout(self):
        """Emit signal to request logout"""
        # Stop camera if running
        if self.capture is not None:
            self.stop_registration()
        self.logout_requested.emit()

    def set_username(self, username):
        """Update the displayed username"""
        self.username = username
        welcome_label = self.findChild(QLabel)
        if welcome_label:
            welcome_label.setText(f"Witaj, {self.username}")