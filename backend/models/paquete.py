from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Paquete(Base):
    __tablename__ = "paquetes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    foto = Column(String(300), nullable=True)
    precio_referencia_suma = Column(Numeric(12, 2), nullable=True)
    precio_costo_real = Column(Numeric(12, 2), nullable=True)
    precio_venta = Column(Numeric(12, 2), nullable=True)
    porcentaje_ganancia = Column(Numeric(5, 2), nullable=True)
    activo = Column(Boolean, default=True)

    productos = relationship("PaqueteProducto", back_populates="paquete", cascade="all, delete-orphan")
    promociones = relationship("PromocionPaquete", back_populates="paquete", cascade="all, delete-orphan")


class PaqueteProducto(Base):
    __tablename__ = "paquete_productos"

    id = Column(Integer, primary_key=True, index=True)
    paquete_id = Column(Integer, ForeignKey("paquetes.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)

    paquete = relationship("Paquete", back_populates="productos")
    producto = relationship("Producto", back_populates="paquete_items")
