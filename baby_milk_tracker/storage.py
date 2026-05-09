from datetime import datetime, timedelta

from baby_milk_tracker.database import get_connection
from baby_milk_tracker.models import Feeding, Pumping

RANGE_DAYS = {
    "day": 1,
    "week": 7,
    "month": 30,
}

def save_feeding(feeding: Feeding) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO feedings (
                created_at,
                feeding_type,
                side,
                duration_min,
                amount_ml
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                feeding.created_at.isoformat(),
                feeding.feeding_type,
                feeding.side,
                feeding.duration_min,
                feeding.amount_ml,
            )
        )

        conn.commit()

def save_pumping(pumping: Pumping) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO pumpings (
                created_at,
                amount_ml,
                side
            )
            VALUES (?, ?, ?)
            """,
            (
                pumping.created_at.isoformat(),
                pumping.amount_ml,
                pumping.side,
            )
        )

        conn.commit()

def get_last_feeding() -> Feeding | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT created_at, feeding_type, side, duration_min, amount_ml
            FROM feedings
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return Feeding(
        created_at=datetime.fromisoformat(row[0]),
        feeding_type=row[1],
        side=row[2],
        duration_min=row[3],
        amount_ml=row[4],
    )

def get_last_pumping() -> Pumping | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT created_at, amount_ml, side
            FROM pumpings
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return Pumping(
        created_at=datetime.fromisoformat(row[0]),
        amount_ml=row[1],
        side=row[2],
    )

def delete_all_records() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM feedings")
        cursor.execute("DELETE FROM pumpings")

        conn.commit()


def get_start_datetime(range_name: str) -> datetime:
    if range_name not in RANGE_DAYS:
        raise ValueError(f"Invalid range name: {range_name}")

    days = RANGE_DAYS[range_name]

    return datetime.now() - timedelta(days=days)

def get_pumpings_since(start_datetime: datetime) -> list[Pumping]:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT created_at, amount_ml, side
            FROM pumpings
            WHERE created_at >= ?
            ORDER BY created_at
            """,
            (start_datetime.isoformat(),),
        )

        rows = cursor.fetchall()

    return [
        Pumping(
            created_at=datetime.fromisoformat(row[0]),
            amount_ml=row[1],
            side=row[2],
        )
        for row in rows
    ]

def get_feedings_since(start_datetime: datetime) -> list[Feeding]:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT created_at, feeding_type, side, duration_min, amount_ml
            FROM feedings
            WHERE created_at >= ?
            ORDER BY created_at
            """,
            (start_datetime.isoformat(),),
        )

        rows = cursor.fetchall()

    return [
        Feeding(
            created_at=datetime.fromisoformat(row[0]),
            feeding_type=row[1],
            side=row[2],
            duration_min=row[3],
            amount_ml=row[4],
        )
        for row in rows
    ]