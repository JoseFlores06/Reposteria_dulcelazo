from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    direccion = Column(String(300), nullable=True)
    correo = Column(String(150), nullable=True)
    telefono = Column(String(20), nullable=True)
    whatsapp = Column(String(20), nullable=True)
    edad_aproximada = Column(Integer, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    ventas = relationship("Venta", back_populates="cliente")
    direcciones = relationship("DireccionCliente", back_populates="cliente", cascade="all, delete-orphan", order_by="DireccionCliente.principal.desc()")
