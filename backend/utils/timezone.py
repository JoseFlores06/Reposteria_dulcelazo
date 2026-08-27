"""
Utilidades de zona horaria para Peru/Lima (UTC-5).
Usar always now_lima() en lugar de datetime.utcnow().
"""
from datetime import datetime
from zoneinfo import ZoneInfo

LIMA_TZ = ZoneInfo("America/Lima")


def now_lima() -> datetime:
    """Fecha y hora actual en Lima, Perú (UTC-5)."""
    return datetime.now(LIMA_TZ).replace(tzinfo=None)


def to_lima(dt: datetime) -> datetime:
    """Convierte un datetime UTC a Lima."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(LIMA_TZ).replace(tzinfo=None)
