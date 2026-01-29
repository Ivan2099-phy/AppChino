"""
Database layer (SQLite)
"""

import sqlite3
import os
from typing import List, Dict, Optional


class Database:
    def __init__(self, db_path: str = "data/chinese_video.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Añadimos check_same_thread=False para permitir multi-hilo
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self._create_tables()
        self._ensure_default_user()

    # ==================================================
    # Inicialización
    # ==================================================

    def _create_tables(self):
        # Videos
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            source_url TEXT,
            file_path TEXT,
            duration REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Words
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            word_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chinese TEXT UNIQUE,
            pinyin TEXT,
            translation TEXT,
            hsk_level INTEGER
        )
        """)

        # Word occurrences (CRÍTICA)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS word_occurrences (
            occurrence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            sentence TEXT NOT NULL,
            start_time REAL,
            end_time REAL,
            FOREIGN KEY(word_id) REFERENCES words(word_id),
            FOREIGN KEY(video_id) REFERENCES videos(video_id)
        )
        """)

        # Users
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
        """)

        # Word status (SRS)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS word_status (
            user_id INTEGER,
            word_id INTEGER,
            status TEXT,
            review_count INTEGER DEFAULT 0,
            PRIMARY KEY(user_id, word_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(word_id) REFERENCES words(word_id)
        )
        """)

        # Video statistics
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_stats (
            video_id INTEGER PRIMARY KEY,
            total_words INTEGER,
            unique_words INTEGER,
            hsk1_count INTEGER,
            hsk2_count INTEGER,
            hsk3_count INTEGER,
            hsk4_count INTEGER,
            hsk5_count INTEGER,
            hsk6_count INTEGER,
            non_hsk_count INTEGER,
            FOREIGN KEY(video_id) REFERENCES videos(video_id)
        )
        """)

        self.conn.commit()

    def _ensure_default_user(self):
        self.cursor.execute("SELECT user_id FROM users LIMIT 1")
        row = self.cursor.fetchone()
        if row is None:
            self.cursor.execute(
                "INSERT INTO users (name) VALUES (?)",
                ("default",)
            )
            self.conn.commit()

    # ==================================================
    # Video
    # ==================================================

    def add_video(
        self,
        title: str,
        source_url: Optional[str] = None,
        file_path: Optional[str] = None,
        duration: Optional[float] = None
    ) -> int:
        self.cursor.execute("""
            INSERT INTO videos (title, source_url, file_path, duration)
            VALUES (?, ?, ?, ?)
        """, (title, source_url, file_path, duration))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_all_videos(self) -> List[Dict]:
        self.cursor.execute("SELECT * FROM videos ORDER BY created_at DESC")
        return [dict(r) for r in self.cursor.fetchall()]

    # ==================================================
    # Words
    # ==================================================

    def add_word(
        self,
        chinese: str,
        pinyin: str = None,
        translation: str = None,
        hsk_level: Optional[int] = None
    ) -> int:
        self.cursor.execute("""
            INSERT OR IGNORE INTO words
            (chinese, pinyin, translation, hsk_level)
            VALUES (?, ?, ?, ?)
        """, (chinese, pinyin, translation, hsk_level))
        self.conn.commit()

        self.cursor.execute(
            "SELECT word_id FROM words WHERE chinese = ?",
            (chinese,)
        )
        return self.cursor.fetchone()["word_id"]

    def get_word(self, word_id: int) -> Dict:
        self.cursor.execute(
            "SELECT * FROM words WHERE word_id = ?",
            (word_id,)
        )
        return dict(self.cursor.fetchone())

    def get_video_words(self, video_id: int) -> List[Dict]:
        # Obtenemos el user_id por defecto (asumimos 1 o buscamos)
        user_id = self.get_default_user_id()
        
        self.cursor.execute("""
            SELECT w.word_id, w.chinese, w.pinyin, w.translation,
                   w.hsk_level, COUNT(o.occurrence_id) AS frequency,
                   COALESCE(ws.status, 'unknown') as status  -- <--- CORRECCIÓN AQUÍ
            FROM words w
            JOIN word_occurrences o ON w.word_id = o.word_id
            LEFT JOIN word_status ws ON w.word_id = ws.word_id AND ws.user_id = ? -- <--- JOIN AQUÍ
            WHERE o.video_id = ?
            GROUP BY w.word_id
        """, (user_id, video_id,)) # <--- Añadir user_id a los parámetros
        return [dict(r) for r in self.cursor.fetchall()]

    # ==================================================
    # Word occurrences
    # ==================================================

    def add_word_occurrence(
        self,
        word_id: int,
        video_id: int,
        sentence: str,
        start_time: float,
        end_time: float
    ):
        self.cursor.execute("""
            INSERT INTO word_occurrences
            (word_id, video_id, sentence, start_time, end_time)
            VALUES (?, ?, ?, ?, ?)
        """, (word_id, video_id, sentence, start_time, end_time))
        self.conn.commit()

    def get_word_occurrences(self, word_id: int, video_id: int) -> List[Dict]:
            # Forzamos que las llaves sean 'sentence' y 'timestamp' para que main_window las encuentre
            self.cursor.execute("""
                SELECT sentence, start_time as timestamp 
                FROM word_occurrences 
                WHERE word_id = ? AND video_id = ?
                LIMIT 10
            """, (word_id, video_id))
            return [dict(r) for r in self.cursor.fetchall()]
    # ==================================================
    # User word status
    # ==================================================

    def get_default_user_id(self) -> int:
        self.cursor.execute("SELECT user_id FROM users LIMIT 1")
        return self.cursor.fetchone()["user_id"]

    def get_word_status(self, user_id: int, word_id: int) -> str:
        self.cursor.execute("""
            SELECT status FROM word_status
            WHERE user_id = ? AND word_id = ?
        """, (user_id, word_id))
        row = self.cursor.fetchone()
        return row["status"] if row else "unknown"

    def set_word_status(
        self,
        user_id: int,
        word_id: int,
        status: str
    ):
        self.cursor.execute("""
            INSERT INTO word_status (user_id, word_id, status)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, word_id)
            DO UPDATE SET status = excluded.status
        """, (user_id, word_id, status))
        self.conn.commit()

    def get_review_count(self, user_id: int, word_id: int) -> int:
        self.cursor.execute("""
            SELECT review_count FROM word_status
            WHERE user_id = ? AND word_id = ?
        """, (user_id, word_id))
        row = self.cursor.fetchone()
        return row["review_count"] if row else 0

    # ==================================================
    # Video statistics
    # ==================================================

    def save_video_stats(self, video_id: int, stats: Dict):
        self.cursor.execute("""
            INSERT OR REPLACE INTO video_stats
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video_id,
            stats["total_words"],
            stats["unique_words"],
            stats["hsk1_count"],
            stats["hsk2_count"],
            stats["hsk3_count"],
            stats["hsk4_count"],
            stats["hsk5_count"],
            stats["hsk6_count"],
            stats["non_hsk_count"]
        ))
        self.conn.commit()

    def get_video_stats(self, video_id: int) -> Dict:
        self.cursor.execute(
            "SELECT * FROM video_stats WHERE video_id = ?",
            (video_id,)
        )
        row = self.cursor.fetchone()
        return dict(row) if row else {}

    # ==================================================
    # Cleanup
    # ==================================================

    def close(self):
        self.conn.close()

