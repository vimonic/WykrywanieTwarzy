import sqlite3
import numpy as np
from .db import Database

class UserModel:
    def __init__(self):
        self.db = Database()

    def add_user(self, name, embedding, role='USER'):
        """
        Dodaje nowego użytkownika z nazwą, embeddingiem i rolą.
        role: 'USER' lub 'ADMIN'
        """
        conn = self.db.get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Users(name, role) VALUES(?,?)', (name, role))
        user_id = cursor.lastrowid
        emb_bytes = embedding.tobytes()
        cursor.execute('INSERT INTO Embeddings(user_id, embedding) VALUES(?,?)', (user_id, emb_bytes))
        conn.commit()
        return user_id

    def add_embedding(self, user_id, embedding):
        """
        Dodaje kolejny embedding do istniejącego user_id.
        """
        conn = self.db.get_conn()
        cursor = conn.cursor()
        emb_bytes = embedding.tobytes()
        cursor.execute(
            'INSERT INTO Embeddings(user_id, embedding) VALUES(?, ?)',
            (user_id, emb_bytes)
        )
        conn.commit()

    def delete_user(self, user_id):
        conn = self.db.get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM Embeddings WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM Users WHERE id = ?', (user_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            conn.rollback()
            return False

    def get_all_embeddings(self):
        conn = self.db.get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, embedding FROM Embeddings')
        results = []
        for user_id, emb_blob in cursor.fetchall():
            emb = np.frombuffer(emb_blob, dtype=np.float32)
            results.append((user_id, emb))
        return results

    # def get_user(self, user_id):
    #     conn = self.db.get_conn()
    #     cursor = conn.cursor()
    #     cursor.execute('SELECT id, name, role FROM Users WHERE id=?', (user_id,))
    #     return cursor.fetchone()
    def get_user(self, user_id):
        """Get user by ID with extra validation"""
        if user_id is None:
            print("Warning: user_id is None!")
            return None

        # Upewnij się, że user_id jest liczbą całkowitą
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            print(f"Warning: user_id '{user_id}' is not a valid integer!")
            # Możesz spróbować szukać po stringu jeśli chcesz
            # ale najprawdopodobniej problem jest gdzie indziej

        conn = self.db.get_conn()
        cursor = conn.cursor()

        # Najpierw sprawdź czy użytkownik istnieje
        cursor.execute('SELECT COUNT(*) FROM Users WHERE id=?', (user_id,))
        count = cursor.fetchone()[0]
        print(f"Found {count} users with id={user_id}")

        cursor.execute('SELECT id, name, role FROM Users WHERE id=?', (user_id,))
        result = cursor.fetchone()
        return result

    def log_event(self, user_id, status):
        from datetime import datetime
        conn = self.db.get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Logs(timestamp, user_id, status) VALUES(?,?,?)',
                       (datetime.now().isoformat(), user_id, status))
        conn.commit()

    def admin_exists(self):
        conn = self.db.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Users WHERE role='ADMIN'")
        count = cursor.fetchone()[0]
        return count > 0

    def get_all_users(self):
        """
        Pobiera wszystkich użytkowników z bazy danych.
        Zwraca listę tupli (id, name, role, embedding_count)
        """
        conn = self.db.get_conn()
        cursor = conn.cursor()

        # Pobierz użytkowników wraz z liczbą embeddingów
        cursor.execute('''
            SELECT u.id, u.name, u.role, COUNT(e.id) as embedding_count
            FROM Users u
            LEFT JOIN Embeddings e ON u.id = e.user_id
            GROUP BY u.id, u.name, u.role
            ORDER BY u.id
        ''')

        return cursor.fetchall()

    def update_user(self, user_id, name=None, role=None):
        """
        Aktualizuje dane użytkownika.
        """
        if not name and not role:
            return False

        conn = self.db.get_conn()
        cursor = conn.cursor()

        try:
            if name and role:
                cursor.execute('UPDATE Users SET name=?, role=? WHERE id=?', (name, role, user_id))
            elif name:
                cursor.execute('UPDATE Users SET name=? WHERE id=?', (name, user_id))
            elif role:
                cursor.execute('UPDATE Users SET role=? WHERE id=?', (role, user_id))

            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating user: {e}")
            conn.rollback()
            return False