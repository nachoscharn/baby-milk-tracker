"""Script para crear usuarios. Uso: python create_user.py <username> <password>"""

import sys

from werkzeug.security import generate_password_hash

from baby_milk_tracker.auth import create_user
from baby_milk_tracker.database import init_db
from baby_milk_tracker.migrations import run_migrations

if len(sys.argv) != 3:
    print("Uso: python create_user.py <username> <password>")
    sys.exit(1)

username = sys.argv[1].strip().lower()
password = sys.argv[2]

init_db()
run_migrations()

try:
    user_id = create_user(username, generate_password_hash(password))
    print(f"Usuario '{username}' creado con id={user_id}")
except Exception as e:
    print(f"Error: {e}")
