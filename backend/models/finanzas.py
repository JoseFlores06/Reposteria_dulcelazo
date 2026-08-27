from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

def _now_lima():
    from utils.timezone import now_lima
    return now_lima()


class PagoColaborador(Base):
    __tablename__ = "pagos_colaboradores"

    id = Column(Integer, primary_key=True, index=True)
    colaborador_id = Column(Integer, ForeignKey("colaboradores.id"), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    fecha = Column(DateTime, default=_now_lima)
    periodo = Column(String(50), nullable=True)
    notas = Column(Text, nullable=True)

    colaborador = relationship("Colaborador", back_populates="pagos")
