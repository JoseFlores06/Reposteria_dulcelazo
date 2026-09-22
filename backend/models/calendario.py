from sqlalchemy import Column, Integer, String, Text, DateTime
from .base import Base


class Calendario(Base):
    __tablename__ = "calendario"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    expiry = Column(DateTime, nullable=True)
    cuenta_email = Column(String(255), nullable=True)
