from baby_milk_tracker.database import (
    get_connection,
    get_placeholder,
    insert_returning_id,
)


def run_migrations() -> None:
    """
    One-time migration: if the users table is empty, seed it from the legacy
    hardcoded USERS dict and move any existing baby_profile + feeding/pumping/
    growth data to the new babies / baby_caregivers schema.
    """
    from baby_milk_tracker.auth import USERS as LEGACY_USERS

    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            return

        for username, password_hash in LEGACY_USERS.items():
            user_id = insert_returning_id(
                cursor,
                f"INSERT INTO users (username, password_hash) VALUES ({placeholder}, {placeholder})",
                (username, password_hash),
            )

        cursor.execute(
            f"SELECT id FROM users WHERE username = {placeholder}",
            (next(iter(LEGACY_USERS)),),
        )
        row = cursor.fetchone()
        if row is None:
            conn.commit()
            return
        user_id = row[0]

        cursor.execute(
            "SELECT first_name, last_name, birth_date, sex FROM baby_profile ORDER BY id DESC LIMIT 1"
        )
        profile_row = cursor.fetchone()

        if profile_row is None:
            conn.commit()
            return

        baby_id = insert_returning_id(
            cursor,
            f"INSERT INTO babies (first_name, last_name, birth_date, sex) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})",
            profile_row,
        )

        cursor.execute(
            f"INSERT INTO baby_caregivers (baby_id, user_id) VALUES ({placeholder}, {placeholder})",
            (baby_id, user_id),
        )

        cursor.execute(
            f"UPDATE feedings SET baby_id = {placeholder} WHERE baby_id IS NULL",
            (baby_id,),
        )
        cursor.execute(
            f"UPDATE pumpings SET baby_id = {placeholder} WHERE baby_id IS NULL",
            (baby_id,),
        )
        cursor.execute(
            f"UPDATE growth_records SET baby_id = {placeholder} WHERE baby_id IS NULL",
            (baby_id,),
        )

        conn.commit()
