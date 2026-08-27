from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class DireccionCliente(Base):
    __tablename__ = "direcciones_clientes"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    etiqueta = Column(String(50), nullable=False, default="casa")
    direccion = Column(String(300), nullable=False)
    distrito = Column(String(100), nullable=True)
    referencia = Column(String(200), nullable=True)
    principal = Column(Boolean, default=False)

    cliente = relationship("Cliente", back_populates="direcciones")
