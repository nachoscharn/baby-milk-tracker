"""Tests para baby_milk_tracker/time_utils.py"""

import pytest

from baby_milk_tracker.time_utils import from_baby_age


@pytest.mark.parametrize(
    "days, expected",
    [
        (0, "0 días."),
        (1, "1 días."),
        (29, "29 días."),
        (30, "1 mes"),
        (31, "1 mes y 1 días."),
        (60, "2 meses"),
        (61, "2 meses y 1 días."),
        (90, "3 meses"),
    ],
)
def test_from_baby_age(days, expected):
    assert from_baby_age(days) == expected
