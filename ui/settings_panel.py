from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from notifications.notification_manager import notification_manager
import smtplib

class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Tytuł
        title = QLabel("Ustawienia Powiadomień")
        title.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title.setStyleSheet('color: #333; margin-bottom: 20px;')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Ramka ustawień
        settings_frame = QFrame()
        settings_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
            }
            QLabel {
                font-family: 'Segoe UI';
                font-size: 12px;
                color: #333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton {
                padding: 8px 16px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        
        settings_layout = QVBoxLayout()
        
        # Email nadawcy
        sender_layout = QHBoxLayout()
        sender_label = QLabel("Email nadawcy (Gmail):")
        self.sender_email = QLineEdit()
        sender_layout.addWidget(sender_label)
        sender_layout.addWidget(self.sender_email)
        settings_layout.addLayout(sender_layout)
        
        # Hasło do aplikacji Gmail
        password_layout = QHBoxLayout()
        password_label = QLabel("Hasło do aplikacji Gmail:")
        self.sender_password = QLineEdit()
        self.sender_password.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.sender_password)
        settings_layout.addLayout(password_layout)
        
        # Informacja o haśle do aplikacji
        password_info = QLabel(
            "Uwaga: Wymagane jest hasło do aplikacji Gmail. "
            "Możesz je wygenerować w ustawieniach bezpieczeństwa swojego konta Google."
        )
        password_info.setWordWrap(True)
        password_info.setStyleSheet("color: #666; font-size: 10px; margin-bottom: 10px;")
        settings_layout.addWidget(password_info)
        
        # Lista odbiorców
        recipients_label = QLabel("Lista odbiorców powiadomień:")
        settings_layout.addWidget(recipients_label)
        
        self.recipients_list = QListWidget()
        self.recipients_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
        """)
        settings_layout.addWidget(self.recipients_list)
        
        # Przyciski do zarządzania listą
        recipients_buttons = QHBoxLayout()
        
        self.add_recipient_input = QLineEdit()
        self.add_recipient_input.setPlaceholderText("Wprowadź adres email...")
        recipients_buttons.addWidget(self.add_recipient_input)
        
        add_button = QPushButton("Dodaj")
        add_button.clicked.connect(self.add_recipient)
        recipients_buttons.addWidget(add_button)
        
        remove_button = QPushButton("Usuń zaznaczony")
        remove_button.clicked.connect(self.remove_recipient)
        recipients_buttons.addWidget(remove_button)
        
        settings_layout.addLayout(recipients_buttons)
        
        # Przycisk zapisz
        save_button = QPushButton("Zapisz ustawienia")
        save_button.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_button)
        
        settings_frame.setLayout(settings_layout)
        layout.addWidget(settings_frame)
        layout.addStretch()
        
        self.setLayout(layout)

    def load_settings(self):
        """Wczytuje zapisane ustawienia"""
        settings = notification_manager.settings
        self.sender_email.setText(settings["sender_email"])
        self.sender_password.setText(settings["sender_password"])
        
        self.recipients_list.clear()
        for email in settings["email_recipients"]:
            self.recipients_list.addItem(email)

    def add_recipient(self):
        """Dodaje nowego odbiorcę do listy"""
        email = self.add_recipient_input.text().strip()
        if email and '@' in email:
            self.recipients_list.addItem(email)
            self.add_recipient_input.clear()
        else:
            QMessageBox.warning(self, "Błąd", "Wprowadź poprawny adres email!")

    def remove_recipient(self):
        """Usuwa zaznaczonego odbiorcę z listy"""
        current_item = self.recipients_list.currentItem()
        if current_item:
            self.recipients_list.takeItem(self.recipients_list.row(current_item))

    def test_gmail_connection(self, email, password):
        """Testuje połączenie z serwerem Gmail"""
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(email, password)
            server.quit()
            return True, "Połączenie z Gmail zostało pomyślnie zweryfikowane!"
        except smtplib.SMTPAuthenticationError:
            return False, "Błąd uwierzytelniania! Sprawdź czy:\n- Email jest poprawny\n- Hasło do aplikacji jest poprawne\n- Masz włączoną weryfikację dwuetapową\n- Używasz hasła do aplikacji, a nie głównego hasła do konta"
        except Exception as e:
            return False, f"Błąd połączenia z Gmail: {str(e)}"

    def save_settings(self):
        """Zapisuje ustawienia i weryfikuje połączenie z Gmail"""
        # Zbierz wszystkie adresy email z listy
        email_recipients = []
        for i in range(self.recipients_list.count()):
            email_recipients.append(self.recipients_list.item(i).text())
        
        sender_email = self.sender_email.text()
        sender_password = self.sender_password.text()
        
        if not sender_email or not sender_password:
            QMessageBox.warning(self, "Błąd", "Email nadawcy i hasło są wymagane!")
            return
            
        if not email_recipients:
            QMessageBox.warning(self, "Błąd", "Dodaj przynajmniej jeden adres email odbiorcy!")
            return

        # Testuj połączenie z Gmail
        success, message = self.test_gmail_connection(sender_email, sender_password)
        
        if success:
            # Aktualizuj ustawienia tylko jeśli połączenie jest udane
            notification_manager.update_settings(
                sender_email,
                sender_password,
                email_recipients
            )
            
            # Wyświetl szczegółowy komunikat sukcesu
            QMessageBox.information(
                self,
                "Sukces",
                f"{message}\n\nUstawienia zostały zapisane dla:\nNadawca: {sender_email}\nOdbiorcy: {', '.join(email_recipients)}"
            )
        else:
            # Wyświetl szczegółowy komunikat błędu
            QMessageBox.critical(
                self,
                "Błąd konfiguracji",
                message
            ) 