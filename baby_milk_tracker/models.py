from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class Feeding:
    created_at: datetime
    feeding_type: str
    side: str | None = None
    duration_min: int | None = None
    amount_ml: int | None = None
    id: int | None = None


@dataclass
class Pumping:
    created_at: datetime
    amount_ml: int
    side: str | None = None
    id: int | None = None


@dataclass
class GrowthRecord:
    created_at: datetime
    weight_kg: float | None = None
    length_cm: float | None = None
    head_circumference_cm: float | None = None
    id: int | None = None


@dataclass
class BabyProfile:
    first_name: str
    last_name: str
    birth_date: datetime
    sex: Literal["female", "male"]
    id: int | None = None


@dataclass
class Appointment:
    appointment_datetime: datetime
    doctor_specialty: str
    location: str | None = None
    id: int | None = None


@dataclass
class MedicalStudy:
    study_date: datetime
    study_type: str
    result: str | None = None
    doctor: str | None = None
    id: int | None = None
