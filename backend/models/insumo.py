from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Enum
from datetime import datetime
import enum
from .base import Base

def _now_lima():
    from utils.timezone import now_lima
    return now_lima()


class UnidadInsumo(str, enum.Enum):
    ml = "ml"
    mg = "mg"
    unidad = "unidad"


class Insumo(Base):
    __tablename__ = "insumos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False, index=True)
    unidad = Column(Enum(UnidadInsumo), nullable=False)
    precio_unitario = Column(Numeric(14, 6), nullable=False)
    stock_actual = Column(Numeric(14, 4), nullable=False, default=0)
    fecha_ingreso = Column(DateTime, default=_now_lima)
    activo = Column(Boolean, default=True)
    # True = ya comprado (cuenta como gasto en Finanzas).
    # False = registrado para armar productos pero aún no comprado (no aparece en Finanzas).
    comprado = Column(Boolean, nullable=False, default=True)
