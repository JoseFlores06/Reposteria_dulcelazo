from sqlalchemy import Column, Integer, Numeric, DateTime, String, Text
from .base import Base


def _now_lima():
    from utils.timezone import now_lima
    return now_lima()


class GastoMarketing(Base):
    __tablename__ = "gastos_marketing"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=_now_lima, nullable=False)
    concepto = Column(String(200), nullable=False)
    canal = Column(String(100), nullable=True)
    monto = Column(Numeric(12, 2), nullable=False)
    notas = Column(Text, nullable=True)
