import sqlite3
from pathlib import Path


DB_PATH = Path("data/baby_milk_tracker.db")


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feedings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                feeding_type TEXT NOT NULL,
                side TEXT,
                duration_min INTEGER,
                amount_ml INTEGER
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pumpings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                amount_ml INTEGER NOT NULL,
                side TEXT
            )
            """
        )

        conn.commit()   