from datetime import datetime, timedelta

from baby_milk_tracker.database import get_connection, get_placeholder
from baby_milk_tracker.models import BabyProfile, Feeding, GrowthRecord, Pumping
from baby_milk_tracker.time_utils import now_argentina

RANGE_DAYS = {"day": 1, "week": 7, "month": 30, "all": None}


def save_feeding(feeding: Feeding) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"""
            INSERT INTO feedings (
                created_at,
                feeding_type,
                side,
                duration_min,
                amount_ml
            )
            VALUES (
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder}
            )
            """,
            (
                feeding.created_at.isoformat(),
                feeding.feeding_type,
                feeding.side,
                feeding.duration_min,
                feeding.amount_ml,
            ),
        )

        conn.commit()


def save_pumping(pumping: Pumping) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"""
            INSERT INTO pumpings (
                created_at,
                amount_ml,
                side
            )
            VALUES (
                {placeholder},
                {placeholder},
                {placeholder}
            )
            """,
            (
                pumping.created_at.isoformat(),
                pumping.amount_ml,
                pumping.side,
            ),
        )

        conn.commit()


def save_growth_record(growth_record: GrowthRecord) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"""
            INSERT INTO growth_records (
                created_at,
                weight_kg,
                length_cm,
                head_circumference_cm
            )
            VALUES (
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder}
            )
            """,
            (
                growth_record.created_at.isoformat(),
                growth_record.weight_kg,
                growth_record.length_cm,
                growth_record.head_circumference_cm,
            ),
        )

        conn.commit()


def get_growth_records() -> list[GrowthRecord]:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                created_at,
                weight_kg,
                length_cm,
                head_circumference_cm
            FROM growth_records
            ORDER BY created_at DESC
            """
        )

        rows = cursor.fetchall()

    return [
        GrowthRecord(
            created_at=datetime.fromisoformat(row[0]),
            weight_kg=row[1],
            length_cm=row[2],
            head_circumference_cm=row[3],
        )
        for row in rows
    ]


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

    return now_argentina() - timedelta(days=days)


def get_pumpings_since(start_datetime: datetime) -> list[Pumping]:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT created_at, amount_ml, side
            FROM pumpings
            WHERE created_at >= {placeholder}
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
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT created_at, feeding_type, side, duration_min, amount_ml
            FROM feedings
            WHERE created_at >= {placeholder}
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


def get_all_feedings() -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, created_at, feeding_type, side, duration_min, amount_ml
            FROM feedings
            ORDER BY created_at DESC
            """
        )

        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "created_at": datetime.fromisoformat(row[1]),
            "feeding_type": row[2],
            "side": row[3],
            "duration_min": row[4],
            "amount_ml": row[5],
        }
        for row in rows
    ]


def get_all_pumpings() -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, created_at, amount_ml, side
            FROM pumpings
            ORDER BY created_at DESC
            """
        )

        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "created_at": datetime.fromisoformat(row[1]),
            "amount_ml": row[2],
            "side": row[3],
        }
        for row in rows
    ]


def delete_feeding(feeding_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"DELETE FROM feedings WHERE id = {placeholder}",
            (feeding_id,),
        )

        conn.commit()


def delete_pumping(pumping_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"DELETE FROM pumpings WHERE id = {placeholder}",
            (pumping_id,),
        )

        conn.commit()


def delete_growth_record(growth_record_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"""
            DELETE FROM growth_records
            WHERE id = {placeholder}
            """,
            (growth_record_id,),
        )

        conn.commit()


def get_baby_profile() -> BabyProfile | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT first_name, last_name, birth_date, sex
            FROM baby_profile
            ORDER BY id DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return BabyProfile(
        first_name=row[0],
        last_name=row[1],
        birth_date=datetime.fromisoformat(row[2]),
        sex=row[3],
    )


def save_baby_profile(profile: BabyProfile) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM baby_profile")

        cursor.execute(
            f"""
            INSERT INTO baby_profile (
                first_name,
                last_name,
                birth_date,
                sex
            )
            VALUES (
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder}
            )
            """,
            (
                profile.first_name,
                profile.last_name,
                profile.birth_date.date().isoformat(),
                profile.sex,
            ),
        )

        conn.commit()


def get_last_growth_record() -> GrowthRecord | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                created_at,
                weight_kg,
                length_cm,
                head_circumference_cm
            FROM growth_records
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return GrowthRecord(
        created_at=datetime.fromisoformat(row[0]),
        weight_kg=row[1],
        length_cm=row[2],
        head_circumference_cm=row[3],
    )
