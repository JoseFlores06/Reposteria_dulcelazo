from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from .base import Base


class UnidadTiempo(str, enum.Enum):
    horas = "horas"
    dias = "dias"
    semanas = "semanas"


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    foto = Column(String(300), nullable=True)
    tiempo_preparacion = Column(Numeric(8, 2), nullable=True)
    unidad_tiempo = Column(Enum(UnidadTiempo), nullable=True)
    precio_costo = Column(Numeric(12, 2), nullable=True)
    precio_venta = Column(Numeric(12, 2), nullable=True)
    porcentaje_ganancia = Column(Numeric(5, 2), nullable=True)
    activo = Column(Boolean, default=True)

    insumos = relationship("ProductoInsumo", back_populates="producto", cascade="all, delete-orphan")
    paquete_items = relationship("PaqueteProducto", back_populates="producto")


class ProductoInsumo(Base):
    __tablename__ = "producto_insumos"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    insumo_id = Column(Integer, ForeignKey("insumos.id"), nullable=False)
    cantidad_necesaria = Column(Numeric(12, 4), nullable=False)

    producto = relationship("Producto", back_populates="insumos")
    insumo = relationship("Insumo")
