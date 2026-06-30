from datetime import datetime

from baby_milk_tracker.models import BabyProfile, GrowthRecord

# Percentiles disponibles: 3, 15, 50, 85, 97
PERCENTILES = [3, 15, 50, 85, 97]

MAX_FINE_WEEKS = 13  # datos semanales precisos hasta semana 13
MAX_MONTHS = 24  # datos mensuales hasta 24 meses
MAX_AGE_DAYS = MAX_MONTHS * 31  # margen para meses de 31 días y años bisiestos

# ---------------------------------------------------------------------------
# OMS — Niñas — Peso por edad (kg)
# Fuente: https://www.who.int/tools/child-growth-standards
# ---------------------------------------------------------------------------

FEMALE_WEIGHT_WEEKLY = {
    0: [2.4, 2.8, 3.2, 3.7, 4.2],
    1: [2.6, 3.0, 3.5, 4.0, 4.5],
    2: [2.8, 3.3, 3.8, 4.4, 4.9],
    3: [3.1, 3.6, 4.1, 4.8, 5.4],
    4: [3.3, 3.8, 4.4, 5.1, 5.7],
    5: [3.5, 4.0, 4.6, 5.4, 6.1],
    6: [3.7, 4.2, 4.8, 5.6, 6.4],
    7: [3.8, 4.4, 5.0, 5.9, 6.7],
    8: [4.0, 4.6, 5.2, 6.1, 6.9],
    9: [4.1, 4.7, 5.4, 6.3, 7.1],
    10: [4.3, 4.9, 5.5, 6.5, 7.3],
    11: [4.4, 5.0, 5.7, 6.7, 7.5],
    12: [4.5, 5.1, 5.8, 6.8, 7.7],
    13: [4.6, 5.3, 6.0, 7.0, 7.9],
}

FEMALE_WEIGHT_MONTHLY = {
    0: [2.4, 2.8, 3.2, 3.7, 4.2],
    1: [2.9, 3.4, 4.0, 4.7, 5.2],
    2: [3.5, 4.0, 4.7, 5.5, 6.1],
    3: [3.9, 4.5, 5.2, 6.1, 6.8],
    4: [4.3, 4.9, 5.7, 6.6, 7.4],
    5: [4.6, 5.3, 6.1, 7.0, 7.9],
    6: [4.9, 5.6, 6.4, 7.4, 8.3],
    7: [5.1, 5.8, 6.7, 7.7, 8.6],
    8: [5.3, 6.1, 7.0, 8.0, 8.9],
    9: [5.5, 6.2, 7.2, 8.2, 9.2],
    10: [5.6, 6.4, 7.4, 8.4, 9.4],
    11: [5.7, 6.6, 7.6, 8.6, 9.7],
    12: [5.8, 6.7, 7.7, 8.8, 9.9],
    13: [6.0, 6.9, 7.9, 9.0, 10.1],
    14: [6.1, 7.0, 8.0, 9.2, 10.3],
    15: [6.2, 7.1, 8.2, 9.4, 10.5],
    16: [6.3, 7.3, 8.3, 9.5, 10.7],
    17: [6.4, 7.4, 8.5, 9.7, 10.9],
    18: [6.5, 7.5, 8.6, 9.9, 11.1],
    19: [6.6, 7.6, 8.7, 10.0, 11.3],
    20: [6.7, 7.7, 8.9, 10.2, 11.5],
    21: [6.8, 7.8, 9.0, 10.3, 11.7],
    22: [6.9, 7.9, 9.1, 10.5, 11.9],
    23: [7.0, 8.0, 9.2, 10.6, 12.0],
    24: [7.1, 8.1, 9.4, 10.8, 12.2],
}

# ---------------------------------------------------------------------------
# OMS — Niñas — Longitud/talla por edad (cm)
# ---------------------------------------------------------------------------

FEMALE_LENGTH_WEEKLY = {
    0: [45.6, 47.2, 49.1, 51.1, 52.7],
    1: [46.7, 48.3, 50.3, 52.3, 54.0],
    2: [47.9, 49.5, 51.5, 53.6, 55.3],
    3: [49.0, 50.7, 52.7, 54.9, 56.6],
    4: [50.0, 51.7, 53.7, 55.9, 57.7],
    5: [50.9, 52.7, 54.6, 56.9, 58.8],
    6: [51.8, 53.6, 55.6, 57.9, 59.8],
    7: [52.7, 54.4, 56.5, 58.8, 60.8],
    8: [53.4, 55.2, 57.3, 59.7, 61.7],
    9: [54.1, 55.9, 58.0, 60.5, 62.6],
    10: [54.8, 56.6, 58.7, 61.3, 63.4],
    11: [55.4, 57.2, 59.4, 62.0, 64.2],
    12: [56.0, 57.8, 60.0, 62.7, 64.9],
    13: [56.5, 58.4, 60.6, 63.3, 65.6],
}

FEMALE_LENGTH_MONTHLY = {
    0: [45.6, 47.2, 49.1, 51.1, 52.7],
    1: [49.8, 51.5, 53.7, 55.9, 57.6],
    2: [52.7, 54.4, 56.7, 59.0, 60.8],
    3: [55.1, 56.9, 59.1, 61.5, 63.4],
    4: [57.0, 58.8, 61.1, 63.6, 65.6],
    5: [58.7, 60.5, 62.9, 65.5, 67.5],
    6: [60.1, 61.9, 64.4, 67.0, 69.1],
    7: [61.4, 63.3, 65.8, 68.5, 70.6],
    8: [62.5, 64.5, 67.0, 69.8, 71.9],
    9: [63.6, 65.5, 68.2, 71.0, 73.2],
    10: [64.6, 66.6, 69.3, 72.2, 74.4],
    11: [65.5, 67.6, 70.4, 73.3, 75.6],
    12: [66.5, 68.5, 71.4, 74.4, 76.7],
    13: [67.4, 69.5, 72.4, 75.4, 77.8],
    14: [68.2, 70.4, 73.4, 76.4, 78.8],
    15: [69.0, 71.2, 74.2, 77.4, 79.8],
    16: [69.8, 72.1, 75.1, 78.3, 80.8],
    17: [70.6, 72.9, 76.0, 79.3, 81.8],
    18: [71.4, 73.7, 76.9, 80.2, 82.7],
    19: [72.2, 74.5, 77.7, 81.1, 83.7],
    20: [72.9, 75.3, 78.6, 82.0, 84.6],
    21: [73.7, 76.0, 79.4, 82.8, 85.5],
    22: [74.4, 76.8, 80.2, 83.7, 86.4],
    23: [75.1, 77.6, 81.0, 84.5, 87.3],
    24: [75.8, 78.3, 81.7, 85.3, 88.1],
}

# ---------------------------------------------------------------------------
# OMS — Varones — Peso por edad (kg)
# ---------------------------------------------------------------------------

MALE_WEIGHT_WEEKLY = {
    0: [2.5, 2.9, 3.3, 3.9, 4.4],
    1: [2.6, 3.0, 3.5, 4.2, 4.8],
    2: [2.8, 3.3, 3.8, 4.6, 5.2],
    3: [3.0, 3.6, 4.2, 5.0, 5.7],
    4: [3.3, 3.9, 4.5, 5.4, 6.2],
    5: [3.5, 4.1, 4.8, 5.8, 6.6],
    6: [3.7, 4.4, 5.1, 6.1, 7.0],
    7: [3.9, 4.6, 5.4, 6.4, 7.3],
    8: [4.0, 4.8, 5.6, 6.7, 7.6],
    9: [4.2, 5.0, 5.8, 6.9, 7.9],
    10: [4.3, 5.1, 6.0, 7.1, 8.1],
    11: [4.4, 5.3, 6.1, 7.3, 8.3],
    12: [4.5, 5.4, 6.3, 7.5, 8.5],
    13: [4.7, 5.5, 6.4, 7.6, 8.7],
}

MALE_WEIGHT_MONTHLY = {
    0: [2.5, 2.9, 3.3, 3.9, 4.4],
    1: [3.2, 3.7, 4.5, 5.3, 6.0],
    2: [3.9, 4.5, 5.2, 6.2, 7.0],
    3: [4.5, 5.1, 6.0, 7.1, 8.0],
    4: [5.0, 5.7, 6.7, 7.8, 8.8],
    5: [5.4, 6.1, 7.1, 8.3, 9.3],
    6: [5.7, 6.5, 7.5, 8.8, 9.8],
    7: [6.0, 6.8, 7.9, 9.2, 10.2],
    8: [6.2, 7.0, 8.1, 9.5, 10.5],
    9: [6.4, 7.2, 8.4, 9.7, 10.8],
    10: [6.6, 7.5, 8.6, 10.0, 11.1],
    11: [6.8, 7.7, 8.9, 10.3, 11.5],
    12: [6.9, 7.8, 9.1, 10.5, 11.7],
    13: [7.1, 8.0, 9.3, 10.8, 12.0],
    14: [7.2, 8.2, 9.5, 11.0, 12.3],
    15: [7.4, 8.4, 9.7, 11.2, 12.5],
    16: [7.5, 8.5, 9.9, 11.5, 12.8],
    17: [7.7, 8.7, 10.1, 11.7, 13.0],
    18: [7.8, 8.9, 10.3, 11.9, 13.3],
    19: [7.9, 9.0, 10.5, 12.1, 13.5],
    20: [8.1, 9.2, 10.6, 12.3, 13.8],
    21: [8.2, 9.3, 10.8, 12.5, 14.0],
    22: [8.3, 9.5, 11.0, 12.7, 14.2],
    23: [8.5, 9.6, 11.2, 12.9, 14.4],
    24: [8.6, 9.8, 11.3, 13.1, 14.6],
}

# ---------------------------------------------------------------------------
# OMS — Varones — Longitud/talla por edad (cm)
# ---------------------------------------------------------------------------

MALE_LENGTH_WEEKLY = {
    0: [46.3, 47.9, 49.9, 51.9, 53.5],
    1: [47.7, 49.3, 51.4, 53.5, 55.1],
    2: [49.0, 50.7, 52.8, 55.0, 56.7],
    3: [50.3, 51.9, 54.2, 56.4, 58.1],
    4: [51.3, 53.0, 55.3, 57.6, 59.4],
    5: [52.2, 54.0, 56.3, 58.7, 60.6],
    6: [53.2, 55.0, 57.3, 59.8, 61.7],
    7: [54.0, 55.9, 58.3, 60.8, 62.7],
    8: [54.8, 56.7, 59.2, 61.7, 63.7],
    9: [55.6, 57.5, 60.0, 62.6, 64.6],
    10: [56.3, 58.3, 60.8, 63.5, 65.5],
    11: [57.0, 59.0, 61.5, 64.3, 66.3],
    12: [57.6, 59.7, 62.2, 65.0, 67.1],
    13: [58.2, 60.3, 62.9, 65.7, 67.9],
}

MALE_LENGTH_MONTHLY = {
    0: [46.3, 47.9, 49.9, 51.9, 53.5],
    1: [51.0, 52.8, 54.7, 56.7, 58.5],
    2: [54.7, 56.4, 58.4, 60.5, 62.3],
    3: [57.6, 59.3, 61.4, 63.6, 65.4],
    4: [60.0, 61.8, 63.9, 66.2, 68.0],
    5: [62.0, 63.8, 66.0, 68.4, 70.2],
    6: [63.8, 65.6, 67.8, 70.3, 72.2],
    7: [65.3, 67.2, 69.5, 72.0, 73.9],
    8: [66.8, 68.7, 71.0, 73.6, 75.6],
    9: [68.1, 70.1, 72.5, 75.2, 77.2],
    10: [69.4, 71.4, 73.8, 76.6, 78.7],
    11: [70.6, 72.6, 75.1, 77.9, 80.1],
    12: [71.7, 73.8, 76.2, 79.2, 81.4],
    13: [72.8, 74.9, 77.4, 80.4, 82.7],
    14: [73.8, 76.0, 78.5, 81.6, 83.9],
    15: [74.8, 77.0, 79.6, 82.7, 85.1],
    16: [75.8, 78.0, 80.6, 83.9, 86.3],
    17: [76.7, 79.0, 81.7, 85.0, 87.4],
    18: [77.7, 80.0, 82.7, 86.1, 88.5],
    19: [78.6, 80.9, 83.7, 87.1, 89.6],
    20: [79.4, 81.8, 84.6, 88.1, 90.7],
    21: [80.3, 82.7, 85.5, 89.0, 91.7],
    22: [81.1, 83.5, 86.4, 90.0, 92.7],
    23: [81.9, 84.4, 87.3, 90.9, 93.7],
    24: [82.7, 85.2, 88.1, 91.8, 94.6],
}

WEIGHT_TABLES = {
    "female": (FEMALE_WEIGHT_WEEKLY, FEMALE_WEIGHT_MONTHLY),
    "male": (MALE_WEIGHT_WEEKLY, MALE_WEIGHT_MONTHLY),
}

LENGTH_TABLES = {
    "female": (FEMALE_LENGTH_WEEKLY, FEMALE_LENGTH_MONTHLY),
    "male": (MALE_LENGTH_WEEKLY, MALE_LENGTH_MONTHLY),
}


# ---------------------------------------------------------------------------
# Lógica de interpolación
# ---------------------------------------------------------------------------


def is_percentile_supported(
    baby_profile: BabyProfile, growth_record: GrowthRecord
) -> bool:
    age_days = (growth_record.created_at.date() - baby_profile.birth_date.date()).days
    return baby_profile.sex in ("female", "male") and 0 <= age_days <= MAX_AGE_DAYS


def _interpolate_reference_values(
    weekly_table: dict[int, list[float]],
    monthly_table: dict[int, list[float]],
    age_days: int,
) -> list[float] | None:
    if age_days < 0 or age_days > MAX_AGE_DAYS:
        return None

    if age_days <= MAX_FINE_WEEKS * 7:
        age_weeks = age_days / 7
        low_week = int(age_weeks)
        high_week = min(low_week + 1, MAX_FINE_WEEKS)
        if low_week == high_week:
            return weekly_table[low_week]
        ratio = age_weeks - low_week
        return [
            low + ratio * (high - low)
            for low, high in zip(weekly_table[low_week], weekly_table[high_week])
        ]
    else:
        age_months = age_days / 30.4375
        low_month = int(age_months)
        high_month = min(low_month + 1, MAX_MONTHS)
        if low_month >= MAX_MONTHS:
            return monthly_table[MAX_MONTHS]
        ratio = age_months - low_month
        return [
            low + ratio * (high - low)
            for low, high in zip(monthly_table[low_month], monthly_table[high_month])
        ]


def _estimate_percentile(
    value: float,
    values_by_percentile: list[float],
) -> int:
    if value <= values_by_percentile[0]:
        return PERCENTILES[0]

    if value >= values_by_percentile[-1]:
        return PERCENTILES[-1]

    for index in range(len(values_by_percentile) - 1):
        low_value = values_by_percentile[index]
        high_value = values_by_percentile[index + 1]

        if low_value <= value <= high_value:
            ratio = (value - low_value) / (high_value - low_value)
            return round(
                PERCENTILES[index]
                + ratio * (PERCENTILES[index + 1] - PERCENTILES[index])
            )

    return 50


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def get_weight_percentile(
    baby_profile: BabyProfile,
    growth_record: GrowthRecord,
) -> int | None:
    if not is_percentile_supported(baby_profile, growth_record):
        return None

    age_days = (growth_record.created_at.date() - baby_profile.birth_date.date()).days
    weekly, monthly = WEIGHT_TABLES[baby_profile.sex]
    reference = _interpolate_reference_values(weekly, monthly, age_days)
    return _estimate_percentile(growth_record.weight_kg, reference)


def get_length_percentile(
    baby_profile: BabyProfile,
    growth_record: GrowthRecord,
) -> int | None:
    if not is_percentile_supported(baby_profile, growth_record):
        return None

    age_days = (growth_record.created_at.date() - baby_profile.birth_date.date()).days
    weekly, monthly = LENGTH_TABLES[baby_profile.sex]
    reference = _interpolate_reference_values(weekly, monthly, age_days)
    return _estimate_percentile(growth_record.length_cm, reference)


def get_growth_age_weeks(
    birth_date: datetime,
    measurement_date: datetime,
) -> int:
    age_days = (measurement_date.date() - birth_date.date()).days
    return round(age_days / 7)


def get_weight_median_curve(sex: str, max_weeks: int) -> list[dict]:
    weekly, monthly = WEIGHT_TABLES.get(sex, WEIGHT_TABLES["female"])
    points = []
    for week in range(min(max_weeks, int(MAX_AGE_DAYS / 7)) + 1):
        ref = _interpolate_reference_values(weekly, monthly, week * 7)
        if ref:
            points.append({"x": week, "y": ref[PERCENTILES.index(50)]})
    return points


def _build_curves(
    weekly_table: dict,
    monthly_table: dict,
    max_weeks: int,
) -> dict[int, list[dict]]:
    curves: dict[int, list[dict]] = {p: [] for p in PERCENTILES}
    for week in range(min(max_weeks, int(MAX_AGE_DAYS / 7)) + 1):
        ref = _interpolate_reference_values(weekly_table, monthly_table, week * 7)
        if ref:
            for i, p in enumerate(PERCENTILES):
                curves[p].append({"x": week, "y": round(ref[i], 2)})
    return curves


def get_weight_percentile_curves(sex: str, max_weeks: int) -> dict[int, list[dict]]:
    weekly, monthly = WEIGHT_TABLES.get(sex, WEIGHT_TABLES["female"])
    return _build_curves(weekly, monthly, max_weeks)


def get_length_percentile_curves(sex: str, max_weeks: int) -> dict[int, list[dict]]:
    weekly, monthly = LENGTH_TABLES.get(sex, LENGTH_TABLES["female"])
    return _build_curves(weekly, monthly, max_weeks)
