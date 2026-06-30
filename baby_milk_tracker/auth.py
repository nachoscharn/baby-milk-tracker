from werkzeug.security import check_password_hash, generate_password_hash

from baby_milk_tracker.database import (
    get_connection,
    get_placeholder,
    insert_returning_id,
)

USERS = {
    "bernardita": generate_password_hash("280426"),
}


def get_user_by_credentials(username: str, password: str) -> int | None:
    """Returns user_id if credentials are valid, None otherwise."""
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, password_hash FROM users WHERE username = {placeholder}",
            (username,),
        )
        row = cursor.fetchone()

    if row is None:
        return None

    user_id, password_hash = row
    if check_password_hash(password_hash, password):
        return user_id

    return None


def check_login(username: str, password: str) -> bool:
    return get_user_by_credentials(username, password) is not None


def create_user(username: str, password_hash: str) -> int:
    """Insert a user row and return the new id."""
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        user_id = insert_returning_id(
            cursor,
            f"INSERT INTO users (username, password_hash) VALUES ({placeholder}, {placeholder})",
            (username, password_hash),
        )
        conn.commit()

    return user_id
