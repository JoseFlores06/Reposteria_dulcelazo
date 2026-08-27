from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

# Importación diferida para evitar circular imports en modelos
def _now_lima():
    from utils.timezone import now_lima
    return now_lima()
from .base import Base


class MetodoPago(str, enum.Enum):
    efectivo = "efectivo"
    yape = "yape"
    plin = "plin"
    transferencia = "transferencia"
    tarjeta = "tarjeta"


class EstadoPago(str, enum.Enum):
    pendiente = "pendiente"
    pagado = "pagado"


class EstadoVenta(str, enum.Enum):
    en_proceso = "en_proceso"
    completada = "completada"
    cancelada = "cancelada"


class ItemTipoVenta(str, enum.Enum):
    producto = "producto"
    paquete = "paquete"
    promocion = "promocion"


class Venta(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    fecha_entrega = Column(DateTime, nullable=True)
    colaborador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_hora = Column(DateTime, default=_now_lima)
    metodo_pago = Column(Enum(MetodoPago), nullable=False)
    estado_pago = Column(Enum(EstadoPago), default=EstadoPago.pendiente)
    estado_venta = Column(Enum(EstadoVenta), default=EstadoVenta.en_proceso)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    total = Column(Numeric(12, 2), nullable=False, default=0)
    notas = Column(Text, nullable=True)
    fuente_marketing = Column(String(50), nullable=True)
    direccion_entrega = Column(String(500), nullable=True)

    cliente = relationship("Cliente", back_populates="ventas")
    colaborador = relationship("Usuario", back_populates="ventas")
    items = relationship("VentaItem", back_populates="venta", cascade="all, delete-orphan")


class VentaItem(Base):
    __tablename__ = "venta_items"

    id = Column(Integer, primary_key=True, index=True)
    venta_id = Column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    # item_id no lleva FK: apunta a productos, paquetes o promociones según item_tipo.
    # Los datos de nombre/precio se copian abajo para que la boleta no cambie si el
    # producto se edita o elimina después.
    item_tipo = Column(Enum(ItemTipoVenta), nullable=False)
    item_id = Column(Integer, nullable=False)
    nombre_snapshot = Column(String(200), nullable=False)
    precio_unitario_snapshot = Column(Numeric(12, 2), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    subtotal = Column(Numeric(12, 2), nullable=False)

    venta = relationship("Venta", back_populates="items")
