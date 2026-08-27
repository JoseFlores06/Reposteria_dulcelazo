from sqlalchemy import Column, Integer, String
from .base import Base


class Empresa(Base):
    __tablename__ = "empresa"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    ruc = Column(String(11), nullable=True)
    numero_yape_plin = Column(String(20), nullable=True)
    nro_cuenta_banco = Column(String(30), nullable=True)
    cci = Column(String(30), nullable=True)
    direccion = Column(String(255), nullable=True)
    telefono = Column(String(20), nullable=True)
    correo = Column(String(100), nullable=True)
    distrito = Column(String(100), nullable=True)
