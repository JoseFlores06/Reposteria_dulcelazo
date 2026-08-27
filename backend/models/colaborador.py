from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Colaborador(Base):
    __tablename__ = "colaboradores"

    id = Column(Integer, primary_key=True, index=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    direccion = Column(String(300), nullable=True)
    correo = Column(String(150), nullable=True)
    telefono = Column(String(20), nullable=True)
    whatsapp = Column(String(20), nullable=True)
    edad_aproximada = Column(Integer, nullable=True)
    rol_descripcion = Column(Text, nullable=True)
    usuario_sistema_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    usuario_sistema = relationship("Usuario", back_populates="colaborador")
    pagos = relationship("PagoColaborador", back_populates="colaborador")
