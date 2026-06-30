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


def get_placeholder() -> str:
    if DATABASE_URL:
        return "%s"

    return "?"


def insert_returning_id(cursor, sql: str, params: tuple) -> int:
    if DATABASE_URL:
        cursor.execute(sql + " RETURNING id", params)
        return cursor.fetchone()[0]
    else:
        cursor.execute(sql, params)
        return cursor.lastrowid


def _add_column_if_not_exists(cursor, table: str, column: str, col_type: str) -> None:
    if DATABASE_URL:
        cursor.execute(
            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"
        )
    else:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except Exception:
            pass


def init_db() -> None:
    with get_connection() as conn:

        id_type = (
            "SERIAL PRIMARY KEY"
            if DATABASE_URL
            else "INTEGER PRIMARY KEY AUTOINCREMENT"
        )
        cursor = conn.cursor()

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id {id_type},
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS babies (
                id {id_type},
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                sex TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS baby_caregivers (
                baby_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (baby_id, user_id)
            )
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS feedings (
                id {id_type},
                created_at TEXT NOT NULL,
                feeding_type TEXT NOT NULL,
                side TEXT,
                duration_min INTEGER,
                amount_ml INTEGER,
                baby_id INTEGER
            )
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS pumpings (
                id {id_type},
                created_at TEXT NOT NULL,
                amount_ml INTEGER NOT NULL,
                side TEXT,
                baby_id INTEGER
            )
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS growth_records (
                id {id_type},
                created_at TEXT NOT NULL,
                weight_kg REAL NOT NULL,
                length_cm REAL NOT NULL,
                head_circumference_cm REAL,
                baby_id INTEGER
            )
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS baby_profile (
                id {id_type},
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                sex TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS appointments (
                id {id_type},
                baby_id INTEGER NOT NULL,
                appointment_datetime TEXT NOT NULL,
                doctor_specialty TEXT NOT NULL,
                location TEXT
            )
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS medical_studies (
                id {id_type},
                baby_id INTEGER NOT NULL,
                study_date TEXT NOT NULL,
                study_type TEXT NOT NULL,
                result TEXT,
                doctor TEXT
            )
            """
        )

        # Add baby_id to existing tables that predate this schema
        _add_column_if_not_exists(cursor, "feedings", "baby_id", "INTEGER")
        _add_column_if_not_exists(cursor, "pumpings", "baby_id", "INTEGER")
        _add_column_if_not_exists(cursor, "growth_records", "baby_id", "INTEGER")

        conn.commit()
