from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


def _now_lima():
    from utils.timezone import now_lima
    return now_lima()


class MermaInsumo(Base):
    """Registro de bajas/mermas de stock de insumos (vencido, dañado, etc.).
    Reduce el stock del insumo SIN afectar su precio unitario."""
    __tablename__ = "mermas_insumos"

    id = Column(Integer, primary_key=True, index=True)
    insumo_id = Column(Integer, ForeignKey("insumos.id", ondelete="CASCADE"), nullable=False)
    cantidad = Column(Numeric(14, 4), nullable=False)
    motivo = Column(String(50), nullable=False, default="vencido")  # 'vencido' | 'otro'
    detalle = Column(String(200), nullable=True)                    # texto libre si motivo = 'otro'
    fecha = Column(DateTime, default=_now_lima)

    insumo = relationship("Insumo")
