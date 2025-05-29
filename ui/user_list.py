from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QHeaderView, QTableWidgetItem, QMessageBox, QDialog,
    QFormLayout, QLineEdit, QComboBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from database.models import UserModel

class UserEditDialog(QDialog):
    """Dialog do edycji informacji o użytkowniku"""

    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data  # (id, name, role, embedding_count)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Edytuj użytkownika")
        self.setModal(True)
        self.setFixedSize(350, 200)

        layout = QFormLayout()

        # Pole nazwy
        self.name_input = QLineEdit()
        self.name_input.setText(self.user_data[1])  # Aktualna nazwa
        self.name_input.setFont(QFont('Segoe UI', 11))
        layout.addRow("Nazwa użytkownika:", self.name_input)

        # Wybór roli
        self.role_combo = QComboBox()
        self.role_combo.addItems(['USER', 'ADMIN'])
        self.role_combo.setCurrentText(self.user_data[2])  # Aktualna rola
        self.role_combo.setFont(QFont('Segoe UI', 11))
        layout.addRow("Rola:", self.role_combo)

        # Etykieta informacyjna
        info_label = QLabel(f"ID: {self.user_data[0]} | Próbki: {self.user_data[3]}")
        info_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addRow(info_label)

        # Przyciski
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Style przycisków
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
        """Zwraca edytowane dane"""
        return {
            'name': self.name_input.text().strip(),
            'role': self.role_combo.currentText()
        }

class UserList(QWidget):
    """Panel listy użytkowników"""

    def __init__(self):
        super().__init__()
        self.user_model = UserModel()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Tytuł
        title_label = QLabel("Lista użytkowników")
        title_label.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title_label.setStyleSheet('color: #333;')
        title_label.setAlignment(Qt.AlignCenter)

        # Przycisk odświeżania
        refresh_btn = QPushButton("Odśwież")
        refresh_btn.setFixedSize(100, 30)
        refresh_btn.clicked.connect(self.refresh_user_list)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005f99;
            }
        """)

        # Tabela
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels(['ID', 'Nazwa', 'Rola', 'Próbki', 'Akcje'])

        # Ustawienia szerokości kolumn
        header = self.user_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.resizeSection(4, 200)  # Stała szerokość dla przycisków akcji

        # Style tabeli
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

        # Układ
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)

        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addLayout(btn_layout)
        layout.addWidget(self.user_table)

        self.setLayout(layout)
        self.refresh_user_list()

    def refresh_user_list(self):
        """Odświeża listę użytkowników"""
        try:
            users = self.user_model.get_all_users()
            self.user_table.setRowCount(len(users))
            self.user_table.verticalHeader().setDefaultSectionSize(60)

            for row, user_data in enumerate(users):
                user_id, name, role, embedding_count = user_data

                # Dodaj dane użytkownika do tabeli
                self.user_table.setItem(row, 0, QTableWidgetItem(str(user_id)))
                self.user_table.setItem(row, 1, QTableWidgetItem(name))
                self.user_table.setItem(row, 2, QTableWidgetItem(role))
                self.user_table.setItem(row, 3, QTableWidgetItem(str(embedding_count)))

                # Utwórz widget z przyciskami akcji
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 5, 5, 5)
                action_layout.setSpacing(5)

                # Przycisk edycji
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
                delete_btn.clicked.connect(lambda checked, uid=user_id, name=name: self.delete_user(uid, name))

                action_layout.addWidget(edit_btn)
                action_layout.addWidget(delete_btn)
                action_layout.addStretch()

                self.user_table.setCellWidget(row, 4, action_widget)

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można załadować listy użytkowników: {str(e)}")

    def edit_user(self, user_id, user_data):
        """Otwiera okno edycji użytkownika"""
        dialog = UserEditDialog(user_data, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()

            # Walidacja danych
            if not new_data['name']:
                QMessageBox.warning(self, "Błąd", "Nazwa użytkownika nie może być pusta.")
                return

            # Aktualizacja użytkownika w bazie danych
            try:
                success = self.user_model.update_user(
                    user_id,
                    name=new_data['name'],
                    role=new_data['role']
                )

                if success:
                    QMessageBox.information(self, "Sukces", "Dane użytkownika zostały zaktualizowane.")
                    self.refresh_user_list()
                else:
                    QMessageBox.warning(self, "Błąd", "Nie udało się zaktualizować danych użytkownika.")

            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Błąd podczas aktualizacji: {str(e)}")

    def delete_user(self, user_id, user_name):
        """Usuwa użytkownika po potwierdzeniu"""
        reply = QMessageBox.question(
            self,
            "Potwierdzenie usunięcia",
            f"Czy na pewno chcesz usunąć użytkownika '{user_name}' (ID: {user_id})?\n\n"
            "Ta operacja jest nieodwracalna i usunie wszystkie dane użytkownika "
            "włącznie z próbkami twarzy.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.user_model.delete_user(user_id)

                if success:
                    QMessageBox.information(self, "Sukces", f"Użytkownik '{user_name}' został usunięty.")
                    self.refresh_user_list()
                else:
                    QMessageBox.warning(self, "Błąd", "Nie udało się usunąć użytkownika.")

            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Błąd podczas usuwania: {str(e)}") 