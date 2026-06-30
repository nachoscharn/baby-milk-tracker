from datetime import datetime

from baby_milk_tracker.models import BabyProfile, GrowthRecord

PERCENTILES = [3, 15, 50, 85, 97]
MIN_AGE_DAYS = 0
MAX_AGE_DAYS = 13 * 7


# OMS - niñas - peso por edad - 0 a 13 semanas
# Valores aproximados en kg

# https://www.who.int/tools/child-growth-standards/standards/weight-for-age?
FEMALE_WEIGHT_FOR_AGE = {
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


# OMS - niñas - longitud por edad - 0 a 13 semanas
# Valores aproximados en cm
FEMALE_LENGTH_FOR_AGE = {
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


def is_percentile_supported(
    baby_profile: BabyProfile, growth_record: GrowthRecord
) -> bool:
    age_days = (growth_record.created_at.date() - baby_profile.birth_date.date()).days
    return baby_profile.sex == "female" and MIN_AGE_DAYS <= age_days <= MAX_AGE_DAYS


def _interpolate_reference_values(
    table: dict[int, list[float]],
    age_days: int,
) -> list[float] | None:
    if age_days < MIN_AGE_DAYS or age_days > MAX_AGE_DAYS:
        return None

    age_weeks = age_days / 7
    low_week = int(age_weeks)
    high_week = min(low_week + 1, 13)

    if low_week == high_week:
        return table[low_week]

    ratio = age_weeks - low_week
    return [
        low_value + ratio * (high_value - low_value)
        for low_value, high_value in zip(table[low_week], table[high_week])
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
            low_percentile = PERCENTILES[index]
            high_percentile = PERCENTILES[index + 1]

            ratio = (value - low_value) / (high_value - low_value)

            return round(low_percentile + ratio * (high_percentile - low_percentile))

    return 50


def get_weight_percentile(
    baby_profile: BabyProfile,
    growth_record: GrowthRecord,
) -> int | None:
    if not is_percentile_supported(baby_profile, growth_record):
        return None

    age_days = (growth_record.created_at.date() - baby_profile.birth_date.date()).days
    reference_values = _interpolate_reference_values(FEMALE_WEIGHT_FOR_AGE, age_days)

    return _estimate_percentile(
        growth_record.weight_kg,
        reference_values,
    )


def get_length_percentile(
    baby_profile: BabyProfile,
    growth_record: GrowthRecord,
) -> int | None:
    if not is_percentile_supported(baby_profile, growth_record):
        return None

    age_days = (growth_record.created_at.date() - baby_profile.birth_date.date()).days
    reference_values = _interpolate_reference_values(FEMALE_LENGTH_FOR_AGE, age_days)

    return _estimate_percentile(
        growth_record.length_cm,
        reference_values,
    )


def get_growth_age_weeks(
    birth_date: datetime,
    measurement_date: datetime,
) -> int:
    age_days = (measurement_date.date() - birth_date.date()).days
    return round(age_days / 7)


def get_weight_median_curve(max_weeks: int) -> list[dict]:
    points = []

    for week in range(min(max_weeks, 13) + 1):
        points.append(
            {
                "x": week,
                "y": FEMALE_WEIGHT_FOR_AGE[week][PERCENTILES.index(50)],
            }
        )

    return points
