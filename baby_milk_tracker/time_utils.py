from datetime import datetime
from zoneinfo import ZoneInfo


ARGENTINA_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")


def now_argentina() -> datetime:
    return datetime.now(ARGENTINA_TIMEZONE)