from datetime import datetime, timedelta

from baby_milk_tracker.database import (
    get_connection,
    get_placeholder,
    insert_returning_id,
)
from baby_milk_tracker.models import (
    Appointment,
    BabyProfile,
    Feeding,
    GrowthRecord,
    MedicalStudy,
    Medication,
    Pumping,
)
from baby_milk_tracker.time_utils import now_argentina

RANGE_DAYS = {"day": 1, "week": 7, "month": 30, "all": None}


# ---------------------------------------------------------------------------
# Baby / caregiver
# ---------------------------------------------------------------------------


def get_baby_for_user(user_id: int) -> BabyProfile | None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT b.id, b.first_name, b.last_name, b.birth_date, b.sex
            FROM babies b
            JOIN baby_caregivers bc ON bc.baby_id = b.id
            WHERE bc.user_id = {placeholder}
            ORDER BY b.id ASC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cursor.fetchone()

    if row is None:
        return None

    profile = BabyProfile(
        first_name=row[1],
        last_name=row[2],
        birth_date=datetime.fromisoformat(row[3]),
        sex=row[4],
    )
    profile.id = row[0]
    return profile


def save_baby(profile: BabyProfile, user_id: int) -> int:
    """Create or update the baby linked to user_id. Returns baby_id."""
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT b.id FROM babies b
            JOIN baby_caregivers bc ON bc.baby_id = b.id
            WHERE bc.user_id = {placeholder}
            LIMIT 1
            """,
            (user_id,),
        )
        row = cursor.fetchone()

        if row:
            baby_id = row[0]
            cursor.execute(
                f"""
                UPDATE babies
                SET first_name = {placeholder},
                    last_name = {placeholder},
                    birth_date = {placeholder},
                    sex = {placeholder}
                WHERE id = {placeholder}
                """,
                (
                    profile.first_name,
                    profile.last_name,
                    profile.birth_date.date().isoformat(),
                    profile.sex,
                    baby_id,
                ),
            )
        else:
            baby_id = insert_returning_id(
                cursor,
                f"""
                INSERT INTO babies (first_name, last_name, birth_date, sex)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                """,
                (
                    profile.first_name,
                    profile.last_name,
                    profile.birth_date.date().isoformat(),
                    profile.sex,
                ),
            )
            cursor.execute(
                f"INSERT INTO baby_caregivers (baby_id, user_id) VALUES ({placeholder}, {placeholder})",
                (baby_id, user_id),
            )

        conn.commit()

    return baby_id


# ---------------------------------------------------------------------------
# Feedings
# ---------------------------------------------------------------------------


def save_feeding(feeding: Feeding, baby_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO feedings (created_at, feeding_type, side, duration_min, amount_ml, baby_id)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                feeding.created_at.isoformat(),
                feeding.feeding_type,
                feeding.side,
                feeding.duration_min,
                feeding.amount_ml,
                baby_id,
            ),
        )
        conn.commit()


def get_last_feeding(baby_id: int) -> Feeding | None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, created_at, feeding_type, side, duration_min, amount_ml
            FROM feedings
            WHERE baby_id = {placeholder}
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (baby_id,),
        )
        row = cursor.fetchone()

    if row is None:
        return None

    return Feeding(
        id=row[0],
        created_at=datetime.fromisoformat(row[1]),
        feeding_type=row[2],
        side=row[3],
        duration_min=row[4],
        amount_ml=row[5],
    )


def finish_feeding(feeding_id: int, duration_min: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE feedings SET duration_min = {placeholder} WHERE id = {placeholder}",
            (duration_min, feeding_id),
        )
        conn.commit()


def get_feedings_since(start_datetime: datetime, baby_id: int) -> list[Feeding]:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, created_at, feeding_type, side, duration_min, amount_ml
            FROM feedings
            WHERE created_at >= {placeholder} AND baby_id = {placeholder}
            ORDER BY created_at DESC
            """,
            (start_datetime.isoformat(), baby_id),
        )
        rows = cursor.fetchall()

    return [
        Feeding(
            id=row[0],
            created_at=datetime.fromisoformat(row[1]),
            feeding_type=row[2],
            side=row[3],
            duration_min=row[4],
            amount_ml=row[5],
        )
        for row in rows
    ]


def get_all_feedings(baby_id: int) -> list[dict]:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, created_at, feeding_type, side, duration_min, amount_ml
            FROM feedings
            WHERE baby_id = {placeholder}
            ORDER BY created_at DESC
            """,
            (baby_id,),
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


def delete_feeding(feeding_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM feedings WHERE id = {placeholder}",
            (feeding_id,),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Pumpings
# ---------------------------------------------------------------------------


def save_pumping(pumping: Pumping, baby_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO pumpings (created_at, amount_ml, side, baby_id)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                pumping.created_at.isoformat(),
                pumping.amount_ml,
                pumping.side,
                baby_id,
            ),
        )
        conn.commit()


def get_last_pumping(baby_id: int) -> Pumping | None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT created_at, amount_ml, side
            FROM pumpings
            WHERE baby_id = {placeholder}
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (baby_id,),
        )
        row = cursor.fetchone()

    if row is None:
        return None

    return Pumping(
        created_at=datetime.fromisoformat(row[0]),
        amount_ml=row[1],
        side=row[2],
    )


def get_pumpings_since(start_datetime: datetime, baby_id: int) -> list[Pumping]:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, created_at, amount_ml, side
            FROM pumpings
            WHERE created_at >= {placeholder} AND baby_id = {placeholder}
            ORDER BY created_at DESC
            """,
            (start_datetime.isoformat(), baby_id),
        )
        rows = cursor.fetchall()

    return [
        Pumping(
            id=row[0],
            created_at=datetime.fromisoformat(row[1]),
            amount_ml=row[2],
            side=row[3],
        )
        for row in rows
    ]


def get_all_pumpings(baby_id: int) -> list[dict]:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, created_at, amount_ml, side
            FROM pumpings
            WHERE baby_id = {placeholder}
            ORDER BY created_at DESC
            """,
            (baby_id,),
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


def delete_pumping(pumping_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM pumpings WHERE id = {placeholder}",
            (pumping_id,),
        )
        conn.commit()


def delete_all_records(baby_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM feedings WHERE baby_id = {placeholder}", (baby_id,)
        )
        cursor.execute(
            f"DELETE FROM pumpings WHERE baby_id = {placeholder}", (baby_id,)
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Growth records
# ---------------------------------------------------------------------------


def save_growth_record(growth_record: GrowthRecord, baby_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO growth_records (created_at, weight_kg, length_cm, head_circumference_cm, baby_id)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                growth_record.created_at.isoformat(),
                growth_record.weight_kg,
                growth_record.length_cm,
                growth_record.head_circumference_cm,
                baby_id,
            ),
        )
        conn.commit()


def get_last_growth_record(baby_id: int) -> GrowthRecord | None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT created_at, weight_kg, length_cm, head_circumference_cm
            FROM growth_records
            WHERE baby_id = {placeholder}
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (baby_id,),
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


def get_last_weight_record(baby_id: int) -> GrowthRecord | None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT created_at, weight_kg, length_cm, head_circumference_cm
            FROM growth_records
            WHERE baby_id = {placeholder} AND weight_kg IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (baby_id,),
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


def get_last_length_record(baby_id: int) -> GrowthRecord | None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT created_at, weight_kg, length_cm, head_circumference_cm
            FROM growth_records
            WHERE baby_id = {placeholder} AND length_cm IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (baby_id,),
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


def get_growth_records(baby_id: int) -> list[dict]:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, created_at, weight_kg, length_cm, head_circumference_cm
            FROM growth_records
            WHERE baby_id = {placeholder}
            ORDER BY created_at DESC
            """,
            (baby_id,),
        )
        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "created_at": datetime.fromisoformat(row[1]),
            "weight_kg": row[2],
            "length_cm": row[3],
            "head_circumference_cm": row[4],
        }
        for row in rows
    ]


def delete_growth_record(growth_record_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM growth_records WHERE id = {placeholder}",
            (growth_record_id,),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------


def save_appointment(appointment: Appointment, baby_id: int) -> int:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        appointment_id = insert_returning_id(
            cursor,
            f"""
            INSERT INTO appointments (baby_id, appointment_datetime, doctor_specialty, location)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                baby_id,
                appointment.appointment_datetime.isoformat(),
                appointment.doctor_specialty,
                appointment.location,
            ),
        )
        conn.commit()

    return appointment_id


def get_appointments(baby_id: int) -> list[dict]:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, appointment_datetime, doctor_specialty, location
            FROM appointments
            WHERE baby_id = {placeholder}
            ORDER BY appointment_datetime ASC
            """,
            (baby_id,),
        )
        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "appointment_datetime": datetime.fromisoformat(row[1]),
            "doctor_specialty": row[2],
            "location": row[3],
        }
        for row in rows
    ]


def get_next_appointment(baby_id: int) -> dict | None:
    placeholder = get_placeholder()
    now = now_argentina().replace(tzinfo=None).isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, appointment_datetime, doctor_specialty, location
            FROM appointments
            WHERE baby_id = {placeholder} AND appointment_datetime >= {placeholder}
            ORDER BY appointment_datetime ASC
            LIMIT 1
            """,
            (baby_id, now),
        )
        row = cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "appointment_datetime": datetime.fromisoformat(row[1]),
        "doctor_specialty": row[2],
        "location": row[3],
    }


def delete_appointment(appointment_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM appointments WHERE id = {placeholder}",
            (appointment_id,),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Medical studies
# ---------------------------------------------------------------------------


def save_medical_study(study: MedicalStudy, baby_id: int) -> int:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        study_id = insert_returning_id(
            cursor,
            f"""
            INSERT INTO medical_studies (baby_id, study_date, study_type, result, doctor)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                baby_id,
                study.study_date.isoformat(),
                study.study_type,
                study.result,
                study.doctor,
            ),
        )
        conn.commit()

    return study_id


def get_medical_studies(baby_id: int) -> list[dict]:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, study_date, study_type, result, doctor
            FROM medical_studies
            WHERE baby_id = {placeholder}
            ORDER BY study_date DESC
            """,
            (baby_id,),
        )
        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "study_date": datetime.fromisoformat(row[1]),
            "study_type": row[2],
            "result": row[3],
            "doctor": row[4],
        }
        for row in rows
    ]


def delete_medical_study(study_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM medical_studies WHERE id = {placeholder}",
            (study_id,),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# User settings
# ---------------------------------------------------------------------------

_DEFAULTS = {"show_pumpings": True, "daily_ml_target": None}


def get_user_settings(user_id: int) -> dict:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT show_pumpings, daily_ml_target FROM user_settings WHERE user_id = {placeholder}",
            (user_id,),
        )
        row = cursor.fetchone()

    if row is None:
        return dict(_DEFAULTS)

    return {
        "show_pumpings": bool(row[0]),
        "daily_ml_target": row[1],
    }


def save_user_settings(user_id: int, settings: dict) -> None:
    from baby_milk_tracker.database import DATABASE_URL

    placeholder = get_placeholder()
    show_pumpings = int(settings.get("show_pumpings", True))
    daily_ml_target = settings.get("daily_ml_target") or None
    if daily_ml_target is not None:
        daily_ml_target = int(daily_ml_target)

    with get_connection() as conn:
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute(
                f"""
                INSERT INTO user_settings (user_id, show_pumpings, daily_ml_target)
                VALUES ({placeholder}, {placeholder}, {placeholder})
                ON CONFLICT (user_id) DO UPDATE
                SET show_pumpings = EXCLUDED.show_pumpings,
                    daily_ml_target = EXCLUDED.daily_ml_target
                """,
                (user_id, show_pumpings, daily_ml_target),
            )
        else:
            cursor.execute(
                f"""
                INSERT OR REPLACE INTO user_settings (user_id, show_pumpings, daily_ml_target)
                VALUES ({placeholder}, {placeholder}, {placeholder})
                """,
                (user_id, show_pumpings, daily_ml_target),
            )
        conn.commit()


# ---------------------------------------------------------------------------
# Medications
# ---------------------------------------------------------------------------


def _row_to_medication(row) -> Medication:
    # row: id, name, dose_amount, frequency_hours, start_datetime, end_datetime, last_dose_at
    med = Medication(
        name=row[1],
        dose_amount=row[2],
        frequency_hours=row[3],
        start_datetime=datetime.fromisoformat(row[4]),
        end_datetime=datetime.fromisoformat(row[5]),
        last_dose_at=datetime.fromisoformat(row[6]) if row[6] else None,
    )
    med.id = row[0]
    return med


def get_active_medications(baby_id: int, user_id: int) -> list[Medication]:
    placeholder = get_placeholder()
    now = now_argentina().replace(tzinfo=None)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, name, dose_amount, frequency_hours, start_datetime, end_datetime, last_dose_at
            FROM medications
            WHERE baby_id = {placeholder} AND user_id = {placeholder}
            ORDER BY name ASC
            """,
            (baby_id, user_id),
        )
        rows = cursor.fetchall()

    return [_row_to_medication(r) for r in rows if datetime.fromisoformat(r[5]) > now]


def get_all_medications(baby_id: int, user_id: int) -> list[Medication]:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, name, dose_amount, frequency_hours, start_datetime, end_datetime, last_dose_at
            FROM medications
            WHERE baby_id = {placeholder} AND user_id = {placeholder}
            ORDER BY start_datetime DESC
            """,
            (baby_id, user_id),
        )
        rows = cursor.fetchall()

    return [_row_to_medication(row) for row in rows]


def get_medication(medication_id: int, user_id: int) -> Medication | None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, name, dose_amount, frequency_hours, start_datetime, end_datetime, last_dose_at
            FROM medications
            WHERE id = {placeholder} AND user_id = {placeholder}
            """,
            (medication_id, user_id),
        )
        row = cursor.fetchone()

    return _row_to_medication(row) if row else None


def save_medication(med: Medication, baby_id: int, user_id: int) -> int:
    placeholder = get_placeholder()
    now = now_argentina().replace(tzinfo=None)

    with get_connection() as conn:
        cursor = conn.cursor()
        med_id = insert_returning_id(
            cursor,
            f"""
            INSERT INTO medications
                (user_id, baby_id, name, dose_amount, frequency_hours, start_datetime, end_datetime, created_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                user_id,
                baby_id,
                med.name,
                med.dose_amount,
                med.frequency_hours,
                med.start_datetime.isoformat(),
                med.end_datetime.isoformat(),
                now.isoformat(),
            ),
        )
        conn.commit()

    return med_id


def record_medication_dose(
    medication_id: int, user_id: int, given_at: datetime
) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE medications SET last_dose_at = {placeholder} WHERE id = {placeholder} AND user_id = {placeholder}",
            (given_at.isoformat(), medication_id, user_id),
        )
        conn.commit()


def delete_medication(medication_id: int, user_id: int) -> None:
    placeholder = get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM medications WHERE id = {placeholder} AND user_id = {placeholder}",
            (medication_id, user_id),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_start_datetime(range_name: str) -> datetime:
    if range_name not in RANGE_DAYS:
        raise ValueError(f"Invalid range name: {range_name}")

    days = RANGE_DAYS[range_name]

    return now_argentina().replace(tzinfo=None) - timedelta(days=days)


# ---------------------------------------------------------------------------
# Legacy — kept for backward compat during transition
# ---------------------------------------------------------------------------


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
            INSERT INTO baby_profile (first_name, last_name, birth_date, sex)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                profile.first_name,
                profile.last_name,
                profile.birth_date.date().isoformat(),
                profile.sex,
            ),
        )
        conn.commit()
