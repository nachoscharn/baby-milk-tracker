from werkzeug.security import check_password_hash, generate_password_hash

USERS = {
    "bernardita": generate_password_hash("280426"),
}


def check_login(username: str, passward: str) -> bool:
    if username not in USERS:
        return False

    return check_password_hash(USERS[username], passward)
