from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont


class UserPanel(QWidget):
    """Panel shown to regular users after successful authentication"""

    logout_requested = pyqtSignal()  # Signal to notify logout request

    def __init__(self, username="User"):
        super().__init__()
        self.username = username
        self.init_ui()

    def init_ui(self):
        """Initialize the user panel UI"""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Welcome header
        welcome_label = QLabel(f"Witaj, {self.username}")
        welcome_label.setFont(QFont('Segoe UI', 24, QFont.Bold))
        welcome_label.setStyleSheet('color: #333;')
        welcome_label.setAlignment(Qt.AlignCenter)

        # Info label
        info_label = QLabel("Zostałeś pomyślnie zalogowany jako użytkownik standardowy.")
        info_label.setFont(QFont('Segoe UI', 12))
        info_label.setStyleSheet('color: #666;')
        info_label.setAlignment(Qt.AlignCenter)

        # Session info
        session_info = QLabel("Twoja sesja jest aktywna.")
        session_info.setFont(QFont('Segoe UI', 10))
        session_info.setStyleSheet('color: #09ab3c;')
        session_info.setAlignment(Qt.AlignCenter)

        # Create logout button
        logout_btn = QPushButton('Wyloguj się')
        logout_btn.setFont(QFont('Segoe UI', 12))
        logout_btn.setFixedSize(200, 50)
        logout_btn.setStyleSheet(
            'QPushButton { background-color: #73198a; color: white; '
            'border: none; border-radius: 5px; }'
            'QPushButton:hover { background-color: #451552; }'
            'QPushButton:pressed { background-color: #662378; }'
        )
        logout_btn.clicked.connect(self.on_logout)

        # Button layout for centering
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(logout_btn)
        btn_layout.addStretch()

        # Add all elements to main layout
        main_layout.addStretch(1)
        main_layout.addWidget(welcome_label)
        main_layout.addWidget(info_label)
        main_layout.addWidget(session_info)
        main_layout.addStretch(1)
        main_layout.addLayout(btn_layout)
        main_layout.addStretch(1)

        self.setLayout(main_layout)

    def on_logout(self):
        """Emit signal to request logout"""
        self.logout_requested.emit()

    def set_username(self, username):
        """Update the displayed username"""
        self.username = username
        welcome_label = self.findChild(QLabel, "welcome_label")
        if welcome_label:
            welcome_label.setText(f"Witaj, {self.username}")