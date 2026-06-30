"""
Crea el bebé en la DB multiuser y linkea todos los registros existentes.
Uso: DATABASE_URL="postgresql://..." python scripts/fix_baby_link.py
"""

import os

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]
placeholder = "%s"

# ── Completá estos datos ──────────────────────────────────────────────────────
BABY_FIRST_NAME = "Nombre"
BABY_LAST_NAME = "Apellido"
BABY_BIRTH_DATE = "2026-01-01"  # formato YYYY-MM-DD
BABY_SEX = "female"  # "female" o "male"
CAREGIVER_USERNAME = "bernardita"
# ─────────────────────────────────────────────────────────────────────────────

with psycopg.connect(DATABASE_URL) as conn:
    cursor = conn.cursor()

    # Buscar usuario
    cursor.execute(
        f"SELECT id FROM users WHERE username = {placeholder}", (CAREGIVER_USERNAME,)
    )
    row = cursor.fetchone()
    if row is None:
        print(f"Usuario '{CAREGIVER_USERNAME}' no encontrado en users")
        exit(1)
    user_id = row[0]
    print(f"Usuario encontrado: id={user_id}")

    # Verificar que no tenga ya un bebé
    cursor.execute(
        f"SELECT baby_id FROM baby_caregivers WHERE user_id = {placeholder}", (user_id,)
    )
    if cursor.fetchone():
        print("Este usuario ya tiene un bebé linkeado, saliendo.")
        exit(0)

    # Crear bebé
    cursor.execute(
        f"""
        INSERT INTO babies (first_name, last_name, birth_date, sex)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
        RETURNING id
        """,
        (BABY_FIRST_NAME, BABY_LAST_NAME, BABY_BIRTH_DATE, BABY_SEX),
    )
    baby_id = cursor.fetchone()[0]
    print(f"Bebé creado: id={baby_id}")

    # Linkear usuario ↔ bebé
    cursor.execute(
        f"INSERT INTO baby_caregivers (baby_id, user_id) VALUES ({placeholder}, {placeholder})",
        (baby_id, user_id),
    )
    print(f"Link creado: baby_id={baby_id} ↔ user_id={user_id}")

    # Backfill de registros sin baby_id
    for table in ("feedings", "pumpings", "growth_records"):
        cursor.execute(
            f"UPDATE {table} SET baby_id = {placeholder} WHERE baby_id IS NULL",
            (baby_id,),
        )
        print(f"  {table}: {cursor.rowcount} registros actualizados")

    conn.commit()
    print("\nListo — todos los registros linkeados al bebé")
