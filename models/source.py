"""
Модель источника данных
"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .base import Base


class Source(Base):
    """Модель источника данных"""
    __tablename__ = 'source'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Source(id={self.id}, name='{self.name}', url='{self.url}')>"

