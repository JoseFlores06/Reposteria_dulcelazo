from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime
from .base import Base

def _now_lima():
    from utils.timezone import now_lima
    return now_lima()


class GastoMarketing(Base):
    __tablename__ = "gastos_marketing"

    id = Column(Integer, primary_key=True, index=True)
    red_social = Column(String(50), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    fecha = Column(DateTime, default=_now_lima)
    descripcion = Column(Text, nullable=True)
    num_contactos = Column(Integer, default=0)
    num_compradores = Column(Integer, default=0)
    periodo = Column(String(50), nullable=True)
