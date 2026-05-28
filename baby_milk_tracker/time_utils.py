from datetime import datetime
from zoneinfo import ZoneInfo

ARGENTINA_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")


def now_argentina() -> datetime:
    return datetime.now(ARGENTINA_TIMEZONE)


def from_baby_age(age_days: int) -> str:
    month = age_days // 30
    days = age_days % 30

    if month == 0:
        return f"{days} días."

    if days == 0:
        return f"{month} mes{'es' if month > 1 else ''}"

    return f"{month} mes{'es' if month > 1 else ''} " f"y {days} días."
