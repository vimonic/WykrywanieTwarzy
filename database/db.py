import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'face_access.db'

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()

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
                FOREIGN KEY(user_id) REFERENCES Users(id)
            )''')
        self.conn.commit()

    def get_conn(self):
        return self.conn