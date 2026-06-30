"""Tests para baby_milk_tracker/percentiles.py"""

from datetime import datetime

import pytest

from baby_milk_tracker.models import BabyProfile, GrowthRecord
from baby_milk_tracker.percentiles import (
    FEMALE_WEIGHT_MONTHLY,
    MALE_LENGTH_MONTHLY,
    MAX_AGE_DAYS,
    PERCENTILES,
    get_length_percentile,
    get_weight_percentile,
    is_percentile_supported,
)

BIRTH = datetime(2026, 1, 1)


def baby(sex="female"):
    return BabyProfile(first_name="B", last_name="S", birth_date=BIRTH, sex=sex)


def record(days_after_birth, weight_kg, length_cm=50.0):
    return GrowthRecord(
        created_at=datetime(2026, 1, 1)
        + __import__("datetime").timedelta(days=days_after_birth),
        weight_kg=weight_kg,
        length_cm=length_cm,
    )


# ---------------------------------------------------------------------------
# is_percentile_supported
# ---------------------------------------------------------------------------


def test_supported_female_day_zero():
    assert is_percentile_supported(baby("female"), record(0, 3.2)) is True


def test_supported_male_day_zero():
    assert is_percentile_supported(baby("male"), record(0, 3.3)) is True


def test_supported_female_at_max_age():
    assert is_percentile_supported(baby("female"), record(MAX_AGE_DAYS, 9.0)) is True


def test_not_supported_past_max_age():
    assert (
        is_percentile_supported(baby("female"), record(MAX_AGE_DAYS + 1, 9.0)) is False
    )


def test_not_supported_before_birth():
    gr = GrowthRecord(
        created_at=datetime(2025, 12, 31),
        weight_kg=3.0,
        length_cm=50.0,
    )
    assert is_percentile_supported(baby(), gr) is False


# ---------------------------------------------------------------------------
# Valores del percentil 50 (mediana OMS) → deben devolver ≈ P50
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sex, months, weight_p50, length_p50",
    [
        ("female", 0, 3.2, 49.1),
        ("female", 6, 6.4, 64.4),
        ("female", 12, 7.7, 71.4),
        ("female", 24, 9.4, 81.7),
        ("male", 0, 3.3, 49.9),
        ("male", 6, 7.5, 67.8),
        ("male", 12, 9.1, 76.2),
        ("male", 24, 11.3, 88.1),
    ],
)
def test_median_values_return_p50(sex, months, weight_p50, length_p50):
    bp = baby(sex)
    days = round(months * 30.4375)
    gr = record(days, weight_p50, length_p50)
    assert get_weight_percentile(bp, gr) == 50
    assert get_length_percentile(bp, gr) == 50


# ---------------------------------------------------------------------------
# Extremos: por debajo de P3 → P3, por encima de P97 → P97
# ---------------------------------------------------------------------------


def test_weight_below_p3_returns_p3():
    bp = baby("female")
    p3_at_birth = FEMALE_WEIGHT_MONTHLY[0][0]
    gr = record(0, p3_at_birth - 1.0)
    assert get_weight_percentile(bp, gr) == PERCENTILES[0]


def test_weight_above_p97_returns_p97():
    bp = baby("female")
    p97_at_birth = FEMALE_WEIGHT_MONTHLY[0][-1]
    gr = record(0, p97_at_birth + 1.0)
    assert get_weight_percentile(bp, gr) == PERCENTILES[-1]


def test_length_below_p3_returns_p3():
    bp = baby("male")
    p3_at_6m = MALE_LENGTH_MONTHLY[6][0]
    days = round(6 * 30.4375)
    gr = record(days, 7.5, p3_at_6m - 5.0)
    assert get_length_percentile(bp, gr) == PERCENTILES[0]


def test_length_above_p97_returns_p97():
    bp = baby("male")
    p97_at_6m = MALE_LENGTH_MONTHLY[6][-1]
    days = round(6 * 30.4375)
    gr = record(days, 7.5, p97_at_6m + 5.0)
    assert get_length_percentile(bp, gr) == PERCENTILES[-1]


# ---------------------------------------------------------------------------
# Niña vs varón usan tablas distintas (distintos valores para mismo input)
# ---------------------------------------------------------------------------


def test_male_female_differ_at_6_months():
    days = round(6 * 30.4375)
    gr = record(days, 7.0, 66.0)
    p_female = get_weight_percentile(baby("female"), gr)
    p_male = get_weight_percentile(baby("male"), gr)
    assert p_female != p_male


# ---------------------------------------------------------------------------
# Transición semanas→meses (semana 13 ≈ mes 3): sin salto brusco
# ---------------------------------------------------------------------------


def test_transition_week13_uses_weekly_table():
    bp = baby("female")
    # Día 91 (exactamente 13 semanas) usa la tabla semanal, donde P50 = 6.0 kg.
    # Día 92 cambia a la tabla mensual, donde el P50 del mes 3 es 5.2 kg.
    # Hay una discontinuidad conocida entre los dos datasets de la OMS.
    gr_91 = record(91, 6.0)
    gr_92 = record(92, 5.2)
    # Con el valor del P50 del dataset correspondiente, ambos deben devolver ~50
    assert abs(get_weight_percentile(bp, gr_91) - 50) <= 5
    assert abs(get_weight_percentile(bp, gr_92) - 50) <= 5


# ---------------------------------------------------------------------------
# Out of range → None
# ---------------------------------------------------------------------------


def test_out_of_range_returns_none():
    bp = baby("female")
    gr = record(MAX_AGE_DAYS + 30, 12.0, 90.0)
    assert get_weight_percentile(bp, gr) is None
    assert get_length_percentile(bp, gr) is None
