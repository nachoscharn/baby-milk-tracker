"""
Gestión de usuarios.

Uso:
  python create_user.py create <username> <password>
  python create_user.py delete <username>
"""

import sys

from werkzeug.security import generate_password_hash

from baby_milk_tracker.auth import create_user
from baby_milk_tracker.database import get_connection, get_placeholder, init_db
from baby_milk_tracker.migrations import run_migrations


def delete_user(username: str) -> bool:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM users WHERE username = {placeholder}", (username,))
        deleted = cursor.rowcount > 0
        conn.commit()

    return deleted


if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(1)

command = sys.argv[1].lower()
username = sys.argv[2].strip().lower()

init_db()
run_migrations()

if command == "create":
    if len(sys.argv) != 4:
        print("Uso: python create_user.py create <username> <password>")
        sys.exit(1)
    password = sys.argv[3]
    try:
        user_id = create_user(username, generate_password_hash(password))
        print(f"Usuario '{username}' creado con id={user_id}")
    except Exception as e:
        print(f"Error: {e}")

elif command == "delete":
    confirm = input(f"¿Eliminar usuario '{username}'? (s/n): ").strip().lower()
    if confirm == "s":
        if delete_user(username):
            print(f"Usuario '{username}' eliminado.")
        else:
            print(f"Usuario '{username}' no encontrado.")
    else:
        print("Cancelado.")

else:
    print(f"Comando desconocido: {command}")
    print(__doc__)
    sys.exit(1)
