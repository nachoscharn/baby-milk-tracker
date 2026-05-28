from dataclasses import dataclass
from datetime import datetime


@dataclass
class Feeding:
    created_at: datetime
    feeding_type: str
    side: str | None = None
    duration_min: int | None = None
    amount_ml: int | None = None


@dataclass
class Pumping:
    created_at: datetime
    amount_ml: int
    side: str | None = None


@dataclass
class GrowthRecord:
    created_at: datetime
    weight_kg: float
    length_cm: float
    head_circumference_cm: float | None = None
