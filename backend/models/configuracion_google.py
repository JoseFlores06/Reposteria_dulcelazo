from sqlalchemy import Column, Integer, String, Text, DateTime
from .base import Base


class ConfiguracionGoogle(Base):
    __tablename__ = "configuracion_google"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    expiry = Column(DateTime, nullable=True)
    cuenta_email = Column(String(255), nullable=True)
