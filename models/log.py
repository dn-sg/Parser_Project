"""
Модель логов парсинга
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Log(Base):
    """Модель лога парсинга"""
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey('source.id'), nullable=False)
    celery_task_id = Column(String(255))
    status = Column(String(20))
    error_code = Column(String(50))
    error_message = Column(Text)
    items_parsed = Column(Integer, default=0)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    duration_seconds = Column(Integer)

    source = relationship("Source", backref="logs")

    def __repr__(self):
        return f"<Log(id={self.id}, source_id={self.source_id}, status='{self.status}')>"

