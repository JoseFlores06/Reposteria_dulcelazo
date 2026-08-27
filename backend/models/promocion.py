from sqlalchemy import Column, Integer, String, Numeric, Boolean, Enum, DateTime, Text
from datetime import datetime
import enum
from .base import Base


class ItemTipoPromocion(str, enum.Enum):
    producto = "producto"
    paquete = "paquete"


class Promocion(Base):
    __tablename__ = "promociones"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    foto = Column(String(300), nullable=True)
    descripcion = Column(Text, nullable=True)
    item_tipo = Column(Enum(ItemTipoPromocion), nullable=False)
    item_id = Column(Integer, nullable=False)
    precio_original = Column(Numeric(12, 2), nullable=False)
    precio_promocion = Column(Numeric(12, 2), nullable=False)
    porcentaje_descuento = Column(Numeric(5, 2), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
