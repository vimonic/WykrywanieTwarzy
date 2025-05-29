import os
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
from pathlib import Path

class NotificationManager:
    def __init__(self):
        self.config_file = Path("config/notification_settings.json")
        self.settings = self.load_settings()
        
        # Ustawienia domyślne dla Gmail
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
    def load_settings(self):
        """Wczytuje ustawienia z pliku konfiguracyjnego"""
        if not self.config_file.exists():
            default_settings = {
                "email_recipients": [],
                "sender_email": "",
                "sender_password": ""  # Hasło do aplikacji Gmail
            }
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, indent=4)
            return default_settings
            
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_settings(self):
        """Zapisuje ustawienia do pliku konfiguracyjnego"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)
    
    def update_settings(self, sender_email, sender_password, email_recipients):
        """Aktualizuje ustawienia powiadomień"""
        self.settings["sender_email"] = sender_email
        self.settings["sender_password"] = sender_password
        self.settings["email_recipients"] = email_recipients
        self.save_settings()
    
    def send_unauthorized_access_notification(self, image_path, confidence_score):
        """Wysyła powiadomienie o nieautoryzowanym dostępie"""
        if not self.settings["email_recipients"] or not self.settings["sender_email"] or not self.settings["sender_password"]:
            print("Błąd: Brak skonfigurowanych ustawień powiadomień")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['Subject'] = 'ALERT: Wykryto próbę nieautoryzowanego dostępu!'
            msg['From'] = self.settings["sender_email"]
            msg['To'] = ', '.join(self.settings["email_recipients"])
            
            # Treść wiadomości
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            text_content = f"""
            Wykryto próbę nieautoryzowanego dostępu!
            
            Data i godzina: {current_time}
            Poziom pewności rozpoznania: {confidence_score:.2%}
            
            W załączniku znajduje się zdjęcie osoby próbującej uzyskać dostęp.
            """
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            
            # Załączanie zdjęcia
            with open(image_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
                msg.attach(img)
            
            # Wysyłanie emaila
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.settings["sender_email"], self.settings["sender_password"])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Błąd podczas wysyłania powiadomienia: {str(e)}")
            return False

# Singleton instance
notification_manager = NotificationManager() 