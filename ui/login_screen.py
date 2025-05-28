import sys
import cv2
import numpy as np
import time
from datetime import datetime, timedelta
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QPushButton, QLabel,
    QVBoxLayout, QWidget, QHBoxLayout, QMessageBox,
    QProgressBar, QFrame, QGridLayout, QStackedWidget
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QFont, QPainter, QPen

from face_recognition.detector import FaceDetector
from face_recognition.embedder import FaceEmbedder
from face_recognition.matcher import FaceMatcher
from database.models import UserModel
from utils.image_utils import preprocess_face
from ui.admin_registration import AdminRegistration
from ui.admin_panel import AdminPanel
from ui.user_panel import UserPanel
from metrics.collector import metrics_collector
from notifications.notification_manager import notification_manager

# Constants for application
AUTH_REQUIRED_TIME = 3.0  # seconds
LOG_THROTTLE_TIME = 60  # seconds
UNAUTHORIZED_DETECTION_TIME = 10.0  # seconds

class FaceMetricsPanel(QFrame):
    """Panel displaying real-time face detection metrics"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet('background-color: #ffffff; border-radius: 8px; border: 1px solid #ddd;')
        self.setFixedHeight(150)

        # Create layout
        layout = QGridLayout()

        # Create metric labels
        self.create_label_pair(layout, "Status:", "Oczekiwanie...", 0, 0)
        self.create_label_pair(layout, "Pewność:", "0.00", 0, 1)
        self.create_label_pair(layout, "Czas weryfikacji:", "0.0s", 1, 0)
        self.create_label_pair(layout, "Rozpoznano:", "Brak", 1, 1)
        self.create_label_pair(layout, "Rozmiar twarzy:", "0x0", 2, 0)
        self.create_label_pair(layout, "Jakość obrazu:", "Niska", 2, 1)

        self.setLayout(layout)

    def create_label_pair(self, layout, title, initial_value, row, col):
        # Title label
        title_label = QLabel(title)
        title_label.setFont(QFont('Segoe UI', 9, QFont.Bold))
        title_label.setStyleSheet('color: #555;')

        # Value label with attribute name derived from title
        attr_name = title.replace(":", "").lower().replace(" ", "_")
        value_label = QLabel(initial_value)
        value_label.setFont(QFont('Segoe UI', 10))
        value_label.setStyleSheet('color: #333; font-weight: 500;')

        # Set the attribute to the instance
        setattr(self, attr_name, value_label)

        # Add to layout
        pair_layout = QVBoxLayout()
        pair_layout.addWidget(title_label)
        pair_layout.addWidget(value_label)
        pair_layout.setSpacing(2)
        layout.addLayout(pair_layout, row, col)

    def update_metrics(self, metrics):
        """Update all metrics from dictionary"""
        for key, value in metrics.items():
            label = getattr(self, key, None)
            if label:
                label.setText(str(value))

                # Set colors based on status
                if key == "status":
                    if "Autoryzowano" in value:
                        label.setStyleSheet('color: #09ab3c; font-weight: bold;')
                    elif "Nieautoryzowany" in value:
                        label.setStyleSheet('color: #e74c3c; font-weight: bold;')
                    elif "Wykrywanie" in value:
                        label.setStyleSheet('color: #3498db; font-weight: bold;')
                    else:
                        label.setStyleSheet('color: #333; font-weight: 500;')

                # Set color for confidence
                if key == "pewność":
                    try:
                        conf = float(value.replace("%", ""))
                        if conf >= 95:
                            label.setStyleSheet('color: #09ab3c; font-weight: bold;')
                        elif conf >= 80:
                            label.setStyleSheet('color: #f39c12; font-weight: bold;')
                        else:
                            label.setStyleSheet('color: #e74c3c; font-weight: bold;')
                    except:
                        pass


class FaceAuthManager:
    """Handles face authentication logic separate from UI"""

    def __init__(self, detector, embedder, matcher, user_model):
        self.detector = detector
        self.embedder = embedder
        self.matcher = matcher
        self.user_model = user_model

        # Authentication state
        self.auth_state = "waiting"  # waiting, detecting, verified, failed
        self.detection_start_time = 0
        self.continuous_detection_time = 0
        self.required_detection_time = AUTH_REQUIRED_TIME
        self.current_user_id = None
        self.current_score = 0.0
        self.face_dims = (0, 0)

        # Logging throttling
        self.last_log_time = {}  # user_id -> timestamp

        # Unauthorized access tracking
        self.unauthorized_detection_start = 0
        self.unauthorized_frame = None
        self.unauthorized_score = 0.0
        
        # Ścieżka do zapisu zdjęć nieautoryzowanych prób
        self.unauthorized_dir = Path("unauthorized_attempts")
        self.unauthorized_dir.mkdir(exist_ok=True)

    def reset_auth_state(self):
        """Reset the authentication state"""
        self.auth_state = "waiting"
        self.detection_start_time = 0
        self.continuous_detection_time = 0
        self.current_user_id = None
        self.current_score = 0.0
        self.face_dims = (0, 0)
        self.unauthorized_detection_start = 0
        self.unauthorized_frame = None
        self.unauthorized_score = 0.0

    def process_frame(self, frame):
        """Process a video frame for face authentication"""
        if frame is None:
            return None, {}

        # Create a copy for display
        display_frame = frame.copy()
        current_time = time.time()

        # Prepare metrics
        metrics = {
            "status": "Oczekiwanie na twarz",
            "pewność": f"{self.current_score * 100:.2f}%",
            "czas_weryfikacji": f"{self.continuous_detection_time:.1f}s",
            "rozpoznano": "Brak",
            "rozmiar_twarzy": f"{self.face_dims[0]}x{self.face_dims[1]}",
            "jakość_obrazu": self.estimate_image_quality(frame)
        }

        # Detect faces
        faces = self.detector.detect_faces(frame)

        # Reset unauthorized tracking if no face detected
        if len(faces) == 0:
            self.unauthorized_detection_start = 0
            self.unauthorized_frame = None
            self.unauthorized_score = 0.0

        # If no face is detected, reset the authentication state
        if len(faces) == 0:
            if self.auth_state != "waiting" and self.auth_state != "verified" and self.auth_state != "failed":
                self.auth_state = "waiting"
                self.continuous_detection_time = 0

            # Draw guidance box in the center when no face is detected
            h, w = display_frame.shape[:2]
            center_x, center_y = w // 2, h // 2
            box_w, box_h = 300, 350
            cv2.rectangle(display_frame,
                          (center_x - box_w // 2, center_y - box_h // 2),
                          (center_x + box_w // 2, center_y + box_h // 2),
                          (200, 200, 200), 2)
            cv2.putText(display_frame, "Umiesc twarz w ramce",
                        (center_x - 150, center_y - box_h // 2 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        else:
            # Process the first detected face
            x, y, w, h = faces[0]
            self.face_dims = (w, h)
            face_img = frame[y:y + h, x:x + w]

            # Get embedding and match
            proc = preprocess_face(face_img)
            emb = self.embedder.get_embedding(proc)
            db_embs = self.user_model.get_all_embeddings()
            user_id, score = self.matcher.match(emb, db_embs)

            # Update current state
            self.current_score = score
            metrics["pewność"] = f"{score * 100:.2f}%"
            metrics["rozmiar_twarzy"] = f"{w}x{h}"

            # Update authentication state based on score and timing
            if score >= self.matcher.threshold:  # Above threshold
                # Reset unauthorized tracking
                self.unauthorized_detection_start = 0
                self.unauthorized_frame = None
                self.unauthorized_score = 0.0

                if self.auth_state == "waiting":
                    # First detection above threshold
                    self.auth_state = "detecting"
                    self.detection_start_time = current_time
                    self.current_user_id = user_id

                elif self.auth_state == "detecting":
                    # Continue detecting
                    if user_id == self.current_user_id:  # Same person consistently detected
                        self.continuous_detection_time = current_time - self.detection_start_time

                        # If detected for required time, verify
                        if self.continuous_detection_time >= self.required_detection_time:
                            self.auth_state = "verified"
                            if user_id is not None:
                                user = self.user_model.get_user(user_id)
                                name = user[1] if user else "Unknown"
                                metrics["rozpoznano"] = name
                                self.log_auth_event(user_id)
                            else:
                                metrics["rozpoznano"] = "Nieznany"
                            metrics_collector.log_auth_attempt(
                                success=True,
                                confidence=self.current_score,
                                detection_time=self.continuous_detection_time
                            )
                    else:
                        # Different person detected, restart
                        self.detection_start_time = current_time
                        self.continuous_detection_time = 0
                        self.current_user_id = user_id
            else:  # Below threshold
                if self.auth_state == "detecting":
                    # Lost detection, reset
                    self.auth_state = "waiting"
                    self.continuous_detection_time = 0

                # Track unauthorized access attempt
                if self.unauthorized_detection_start == 0:
                    self.unauthorized_detection_start = current_time
                    self.unauthorized_frame = frame.copy()
                    self.unauthorized_score = score
                elif current_time - self.unauthorized_detection_start >= UNAUTHORIZED_DETECTION_TIME:
                    # Zapisz zdjęcie nieautoryzowanej próby
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_path = self.unauthorized_dir / f"unauthorized_{timestamp}.jpg"
                    cv2.imwrite(str(image_path), self.unauthorized_frame)
                    
                    # Zapisz do bazy danych
                    _, img_encoded = cv2.imencode('.jpg', self.unauthorized_frame)
                    self.user_model.log_unauthorized_access(img_encoded.tobytes(), self.unauthorized_score)
                    
                    # Wyślij powiadomienie email
                    notification_manager.send_unauthorized_access_notification(
                        str(image_path),
                        self.unauthorized_score
                    )
                    
                    # Reset tracking
                    self.unauthorized_detection_start = 0
                    self.unauthorized_frame = None
                    self.unauthorized_score = 0.0

                # Log failed authentication attempt (rate-limited)
                now = time.time()
                if not hasattr(self, 'last_failed_log') or (now - self.last_failed_log) > 2.0:
                    metrics_collector.log_auth_attempt(
                        success=False,
                        confidence=score
                    )
                    self.last_failed_log = now

            # Draw rectangle around face with color based on state
            if self.auth_state == "waiting":
                color = (255, 128, 0)  # Orange
                metrics["status"] = "Wykrywanie twarzy"
            elif self.auth_state == "detecting":
                color = (0, 128, 255)  # Blue
                metrics["status"] = f"Wykrywanie twarzy..."
            elif self.auth_state == "verified":
                if user_id is not None:
                    color = (0, 255, 0)  # Green
                    user = self.user_model.get_user(user_id)
                    name = user[1] if user else "Unknown"
                    metrics["status"] = f"Autoryzowano: {name}"
                    metrics["rozpoznano"] = name
                else:
                    color = (0, 0, 255)  # Red
                    metrics["status"] = "Nieautoryzowany uzytkownik"
                    metrics["rozpoznano"] = "Nieznany"
            elif self.auth_state == "failed":
                color = (0, 0, 255)  # Red
                metrics["status"] = "Odmowa dostępu"

            # Draw rectangle and status
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, 2)

            # Add multiple status lines
            y_offset = y - 10
            if y_offset < 20:
                y_offset = y + h + 25

            # Add confidence bar under the face
            confidence_width = int(w * score)
            confidence_height = 5
            confidence_y = y + h + 5

            # Background bar (gray)
            cv2.rectangle(display_frame, (x, confidence_y), (x + w, confidence_y + confidence_height),
                          (100, 100, 100), -1)

            # Filled confidence bar (colored based on value)
            confidence_color = (0, 255, 0) if score >= 0.9 else (0, 165, 255) if score >= 0.7 else (0, 0, 255)
            cv2.rectangle(display_frame, (x, confidence_y), (x + confidence_width, confidence_y + confidence_height),
                          confidence_color, -1)

            # Status text with background
            status_text = ""
            if self.auth_state == "waiting":
                status_text = "Wykrywanie twarzy..."
            elif self.auth_state == "detecting":
                status_text = f"Weryfikacja: {int(self.continuous_detection_time)}/{int(self.required_detection_time)}s"
            elif self.auth_state == "verified":
                if user_id is not None:
                    user = self.user_model.get_user(user_id)
                    name = user[1] if user else "Unknown"
                    status_text = f"Zalogowano: {name}"
                else:
                    status_text = "Nieautoryzowany uzytkownik"
            elif self.auth_state == "failed":
                status_text = "Odmowa dostępu"

            # Calculate background rectangle for text
            text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(display_frame, (x, y_offset - 20), (x + text_size[0] + 10, y_offset + 5),
                          (0, 0, 0), -1)

            # Draw text
            cv2.putText(display_frame, status_text, (x + 5, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Score text
            score_text = f"Pewnosc: {score:.2f}"
            cv2.putText(display_frame, score_text, (x, confidence_y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return display_frame, metrics

    def quality_to_score(self, quality_str):
        """Convert quality string to numeric score (0-100)"""
        quality_map = {
            "Wysoka": 90,
            "Średnia": 60,
            "Niska (kontrast)": 30,
            "Niska (oświetlenie)": 20,
            "Nieaktywna": 0
        }
        return quality_map.get(quality_str, 50)

    def log_auth_event(self, user_id):
        """Log authentication event with throttling to prevent database bloat"""
        current_time = datetime.now()

        # Check if we should log this event (throttle by user_id)
        last_log = self.last_log_time.get(user_id)
        if last_log is None or (current_time - last_log) > timedelta(seconds=LOG_THROTTLE_TIME):
            # Get current frame and encode it
            ret, frame = self.detector.get_current_frame()
            if ret:
                _, img_encoded = cv2.imencode('.jpg', frame)
                self.user_model.log_event(
                    user_id,
                    'success',
                    img_encoded.tobytes(),
                    self.current_score
                )
            else:
                self.user_model.log_event(user_id, 'success')
            self.last_log_time[user_id] = current_time

    def estimate_image_quality(self, image):
        """Estimate the quality of an image based on brightness and contrast"""
        if image is None or image.size == 0:
            return "Nieaktywna"

        # Calculate brightness and contrast
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        brightness = np.mean(gray)
        contrast = np.std(gray)

        # Determine quality based on these metrics
        if brightness < 40 or brightness > 220:
            return "Niska (oświetlenie)"
        elif contrast < 20:
            return "Niska (kontrast)"
        elif contrast > 80 and brightness > 100:
            return "Wysoka"
        else:
            return "Średnia"


class LoginScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Face Access - Logowanie')
        self.resize(900, 700)
        self.setStyleSheet('background-color: #f0f2f5;')

        # Initialize dependencies
        self.detector = FaceDetector()
        self.embedder = FaceEmbedder()
        self.matcher = FaceMatcher()  # threshold=0.90 is default
        self.user_model = UserModel()

        # Create authentication manager
        self.auth_manager = FaceAuthManager(self.detector, self.embedder, self.matcher, self.user_model)

        # Set up UI components
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create stacked widget for different screens
        self.stack = QStackedWidget()

        # Create main login page
        self.login_page = QWidget()
        self.init_login_ui()

        # Add the pages to stack
        self.stack.addWidget(self.login_page)

        # Main layout for central widget
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.addWidget(self.stack)

        # Timer and flags
        self.capture = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self.update_ui_elements)
        self.ui_update_timer.setInterval(100)  # Update UI at 10Hz

        # Authentication timer to handle panel transition
        self.auth_timer = QTimer()
        self.auth_timer.setSingleShot(True)
        self.auth_timer.timeout.connect(self.handle_authentication_result)

        # Animation
        self.loading_dots = ""
        self.loading_timer = 0

        self.verified_user_id = None

    def init_login_ui(self):
        """Initialize all UI elements for the login screen"""
        # Title and buttons
        title = QLabel('Face Access System')
        title.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        title.setStyleSheet('color: #333; padding: 15px;')

        back_btn = QPushButton('Wróć')
        exit_btn = QPushButton('Wyjście')
        for btn in (back_btn, exit_btn):
            btn.setFont(QFont('Segoe UI', 10))
            btn.setFixedSize(80, 30)
            btn.setStyleSheet(
                'QPushButton { background-color: #73198a; color: white; border: none; border-radius: 5px; }'
                'QPushButton:hover { background-color: #451552; }'
                'QPushButton:pressed { background-color: #662378; }'
            )
        back_btn.clicked.connect(self.stop_camera)
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

        # Progress bar for authentication
        self.auth_progress = QProgressBar()
        self.auth_progress.setFixedSize(800, 15)
        self.auth_progress.setTextVisible(False)
        self.auth_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #eee;
            }
            QProgressBar::chunk {
                background-color: #09ab3c;
                border-radius: 3px;
            }
        """)
        self.auth_progress.setVisible(False)
        self.auth_progress.setValue(0)

        # Create metrics panel
        self.metrics_panel = FaceMetricsPanel()

        # Control buttons
        self.start_btn = QPushButton('Rozpocznij wykrywanie twarzy')
        self.start_btn.setFont(QFont('Segoe UI', 14))
        self.start_btn.setFixedSize(330, 50)
        self.start_btn.setStyleSheet(
            'QPushButton { background-color: #09ab3c; color: white; border: none; border-radius: 8px; }'
            'QPushButton:hover { background-color: #0e4a21; }'
            'QPushButton:pressed { background-color: #158a3a; }'
        )
        self.start_btn.clicked.connect(self.start_camera)

        # Admin registration related elements
        self.admin_exists = self.user_model.admin_exists()
        self.admin_label = QLabel('Brak zarejestrowanego Admina. Czy chcesz go zarejestrować?')
        self.admin_label.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        self.admin_label.setStyleSheet('color: red;')
        self.admin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.reg_btn = QPushButton('Zarejestruj Admina')
        self.reg_btn.setFont(QFont('Segoe UI', 14))
        self.reg_btn.setFixedSize(200, 50)
        self.reg_btn.setStyleSheet(
            'QPushButton { background-color: #ff8800; color: white; border: none; border-radius: 8px; }'
            'QPushButton:hover { background-color: #cc6e00; }'
            'QPushButton:pressed { background-color: #995500; }'
        )
        self.reg_btn.clicked.connect(self.open_registration)

        # Layouts
        video_layout = QVBoxLayout()
        video_layout.addWidget(self.video_label, alignment=Qt.AlignCenter)
        video_layout.addWidget(self.auth_progress, alignment=Qt.AlignCenter)

        metrics_layout = QHBoxLayout()
        metrics_layout.addStretch()
        metrics_layout.addWidget(self.metrics_panel)
        metrics_layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        if not self.admin_exists:
            btn_layout.addWidget(self.reg_btn)
        else:
            btn_layout.addWidget(self.start_btn)
        btn_layout.addStretch()

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        if not self.admin_exists:
            main_layout.addWidget(self.admin_label)
        main_layout.addLayout(video_layout)
        main_layout.addSpacing(15)
        main_layout.addLayout(metrics_layout)
        main_layout.addSpacing(15)
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()

        self.login_page.setLayout(main_layout)

        # Initialize metrics panel with default values
        self.metrics_panel.update_metrics({
            "status": "Oczekiwanie na rozpoczęcie",
            "pewność": "0.00%",
            "czas_weryfikacji": "0.0s",
            "rozpoznano": "Brak",
            "rozmiar_twarzy": "0x0",
            "jakość_obrazu": "Nieaktywna"
        })
        self.metrics_panel.setVisible(False)

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

    def start_camera(self):
        """Start the camera feed"""
        if self.capture is None:
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                QMessageBox.warning(self, "Błąd kamery", "Nie można otworzyć kamery")
                self.capture = None
                return
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 450)
            self.start_btn.setEnabled(False)
            self.reg_btn.hide() if hasattr(self, 'reg_btn') else None
            self.timer.start(30)
            self.ui_update_timer.start()
            self.metrics_panel.setVisible(True)
            self.auth_progress.setVisible(True)
            self.auth_manager.reset_auth_state()

    def stop_camera(self):
        """Stop the camera feed"""
        if self.capture is not None:
            self.timer.stop()
            self.ui_update_timer.stop()
            self.capture.release()
            self.capture = None
            self.video_label.setPixmap(self.placeholder)
            self.start_btn.setEnabled(True)
            self.metrics_panel.setVisible(False)
            self.auth_progress.setVisible(False)
            self.auth_manager.reset_auth_state()

    def update_ui_elements(self):
        """Update UI elements that need frequent updates independent of frame rate"""
        # Update loading dots animation
        if self.auth_manager.auth_state == "detecting":
            self.loading_timer += 0.1
            if self.loading_timer >= 0.5:  # Update dots every 500ms
                self.loading_timer = 0
                self.loading_dots = "." * ((len(self.loading_dots) + 1) % 4)

        # Update progress bar for continuous detection
        if self.auth_manager.auth_state == "detecting":
            progress = min(100, int((self.auth_manager.continuous_detection_time /
                                     self.auth_manager.required_detection_time) * 100))
            self.auth_progress.setValue(progress)
        elif self.auth_manager.auth_state == "verified":
            self.auth_progress.setValue(100)
        elif self.auth_manager.auth_state == "failed":
            # Use red progress bar for failed
            self.auth_progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background: #eee;
                }
                QProgressBar::chunk {
                    background-color: #e74c3c;
                    border-radius: 3px;
                }
            """)
            self.auth_progress.setValue(100)
        else:
            # Reset to green when not in a failed state
            self.auth_progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background: #eee;
                }
                QProgressBar::chunk {
                    background-color: #09ab3c;
                    border-radius: 3px;
                }
            """)
            self.auth_progress.setValue(0)

    def update_frame(self):
        """Process and display the next camera frame"""
        if self.capture is None:
            return

        ret, frame = self.capture.read()
        if not ret:
            return

        # Process frame with auth manager
        display_frame, metrics = self.auth_manager.process_frame(frame)

        # Zapisz ID użytkownika, gdy weryfikacja jest zakończona
        if (self.auth_manager.auth_state == "verified" and 
            self.auth_manager.current_user_id is not None and 
            not self.auth_timer.isActive()):  # Dodany warunek sprawdzający czy timer nie jest aktywny
            
            self.verified_user_id = self.auth_manager.current_user_id
            print(f"✅ Zapisano verified_user_id: {self.verified_user_id}")
            
            # Start timer for panel transition
            self.auth_timer.start(1000)  # Wait 1 second before transitioning for better UX

        # Add loading dots to status if detecting
        if self.auth_manager.auth_state == "detecting" and "status" in metrics:
            metrics["status"] = metrics["status"] + self.loading_dots

        # Update metrics panel
        self.metrics_panel.update_metrics(metrics)

        # Convert to QImage and display
        rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))

    def handle_authentication_result(self):
        """Handle transition to appropriate panel based on authentication result"""
        # if self.auth_manager.auth_state != "verified" or self.auth_manager.current_user_id is None:
        #     return
        # Użyj zapisanego ID użytkownika zamiast polegać na bieżącym stanie auth_manager
        if self.verified_user_id is None:
            print("❌ verified_user_id is None!")
            return

        # Stop camera and timers
        self.stop_camera()

        # Get user details
        # user_id = self.auth_manager.current_user_id
        user_id = self.verified_user_id
        print(f"🔍 Próba pobrania użytkownika z ID: {user_id}")
        user = self.user_model.get_user(user_id)

        if user is None:
            QMessageBox.warning(self, "Błąd", "Nie można znaleźć użytkownika w bazie danych")
            return

        # Extract user information
        # user_id, username, is_admin = user[0], user[1], user[3]  # Assuming index 3 contains is_admin flag
        user_id, username, role = user[0], user[1], user[2]
        is_admin = (role.upper() == 'ADMIN')

        print(f"👤 Szczegóły użytkownika - id: {user_id}, name: {username}, role: {role}, is_admin: {is_admin}")

        # Create and display the appropriate panel based on user role
        if is_admin:
            self.show_admin_panel(username)
        else:
            self.show_user_panel(username)

    def show_admin_panel(self, username):
        """Show the admin panel"""
        # Create admin panel if it doesn't exist
        admin_panel = AdminPanel(username)
        admin_panel.logout_requested.connect(self.handle_logout)

        # Add to stack and switch to it
        self.stack.addWidget(admin_panel)
        self.stack.setCurrentWidget(admin_panel)

    def show_user_panel(self, username):
        """Show the regular user panel"""
        # Create user panel
        user_panel = UserPanel(username)
        user_panel.logout_requested.connect(self.handle_logout)

        # Add to stack and switch to it
        self.stack.addWidget(user_panel)
        self.stack.setCurrentWidget(user_panel)

    def handle_logout(self):
        """Handle logout request from any panel"""
        # Remove the current panel from stack
        current_widget = self.stack.currentWidget()
        if current_widget != self.login_page:
            self.stack.removeWidget(current_widget)
            current_widget.deleteLater()

        # Reset auth manager
        self.auth_manager.reset_auth_state()

        # Return to login page
        self.stack.setCurrentWidget(self.login_page)
        self.start_btn.setEnabled(True)

    def open_registration(self):
        """Open the admin registration window"""
        self.hide()
        self.reg_window = AdminRegistration()
        self.reg_window.registration_complete.connect(self.on_registration_complete)
        self.reg_window.show()

    def on_registration_complete(self):
        """Handle completion of admin registration"""
        self.show()
        # Refresh UI to show login button if admin was registered
        if self.user_model.admin_exists():
            self.admin_label.hide()
            self.reg_btn.hide()
            self.start_btn.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginScreen()
    window.show()
    sys.exit(app.exec_())