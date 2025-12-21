"""
Модель новостей RBC
"""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class RBCNews(Base):
    """Модель новости RBC"""
    __tablename__ = 'rbc_news'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey('source.id'), nullable=False)
    title = Column(Text)
    url = Column(Text, unique=True)
    text = Column(Text)
    parsed_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("Source", backref="rbc_news")

    def __repr__(self):
        return f"<RBCNews(id={self.id}, title='{self.title[:50] if self.title else None}...')>"

