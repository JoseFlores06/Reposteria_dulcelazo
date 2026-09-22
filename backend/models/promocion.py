from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Promocion(Base):
    __tablename__ = "promociones"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    foto = Column(String(300), nullable=True)
    descripcion = Column(Text, nullable=True)
    precio_original = Column(Numeric(12, 2), nullable=False)
    precio_promocion = Column(Numeric(12, 2), nullable=False)
    porcentaje_descuento = Column(Numeric(5, 2), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    productos = relationship("Producto", back_populates="promocion")
    paquetes = relationship("PromocionPaquete", back_populates="promocion", cascade="all, delete-orphan")


class PromocionPaquete(Base):
    __tablename__ = "promocion_paquetes"

    id = Column(Integer, primary_key=True, index=True)
    promocion_id = Column(Integer, ForeignKey("promociones.id", ondelete="CASCADE"), nullable=False)
    paquete_id = Column(Integer, ForeignKey("paquetes.id", ondelete="CASCADE"), nullable=False)
    descuento_adicional = Column(Numeric(5, 2), nullable=False, default=0)
    activo = Column(Boolean, default=True)

    promocion = relationship("Promocion", back_populates="paquetes")
    paquete = relationship("Paquete", back_populates="promociones")
