import os
import sqlite3
from pathlib import Path

import psycopg

DB_PATH = Path("data/baby_milk_tracker.db")

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if DATABASE_URL:
        return psycopg.connect(DATABASE_URL)

    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feedings (
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
                created_at TEXT NOT NULL,
                amount_ml INTEGER NOT NULL,
                side TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS growth_records (
                id SERIAL PRIMARY KEY,
                created_at TEXT NOT NULL,
                weight_kg REAL NOT NULL,
                length_cm REAL NOT NULL,
                head_circumference_cm REAL
            )
            """
        )

        conn.commit()


def get_placeholder() -> str:
    if DATABASE_URL:
        return "%s"

    return "?"
