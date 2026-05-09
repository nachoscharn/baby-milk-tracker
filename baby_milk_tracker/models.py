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