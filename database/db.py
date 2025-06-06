import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'face_access.db'

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()
        self.update_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Użytkownicy: dodamy kolumnę "role"
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'USER'
            )''')
        # Embeddingi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                embedding BLOB,
                FOREIGN KEY(user_id) REFERENCES Users(id)
            )''')
        # Logi dostępu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_id INTEGER,
                status TEXT,
                image BLOB,
                confidence REAL,
                FOREIGN KEY(user_id) REFERENCES Users(id)
            )''')
        # Nieuprawnione próby dostępu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS UnauthorizedAccess (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                image BLOB NOT NULL,
                confidence REAL NOT NULL
            )''')
        self.conn.commit()

    def update_tables(self):
        """Aktualizuje strukturę istniejących tabel"""
        cursor = self.conn.cursor()
        try:
            # Sprawdź czy kolumny już istnieją
            cursor.execute('PRAGMA table_info(Logs)')
            columns = [column[1] for column in cursor.fetchall()]
            
            # Dodaj kolumnę image jeśli nie istnieje
            if 'image' not in columns:
                cursor.execute('ALTER TABLE Logs ADD COLUMN image BLOB')
            
            # Dodaj kolumnę confidence jeśli nie istnieje
            if 'confidence' not in columns:
                cursor.execute('ALTER TABLE Logs ADD COLUMN confidence REAL')
            
            self.conn.commit()
        except Exception as e:
            print(f"Error updating tables: {e}")
            self.conn.rollback()

    def get_conn(self):
        return self.conn