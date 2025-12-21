"""
Модель акций SmartLab
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class SmartlabStock(Base):
    """Модель акции SmartLab"""
    __tablename__ = 'smartlab_stocks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey('source.id'), nullable=False)
    name = Column(String(255))
    ticker = Column(String(20))
    last_price_rub = Column(Numeric(10, 2))
    price_change_percent = Column(Numeric(10, 2))
    volume_mln_rub = Column(Numeric(20, 2))
    change_week_percent = Column(Numeric(10, 2))
    change_month_percent = Column(Numeric(10, 2))
    change_ytd_percent = Column(Numeric(10, 2))
    change_year_percent = Column(Numeric(10, 2))
    capitalization_bln_rub = Column(Numeric(20, 2))
    capitalization_bln_usd = Column(Numeric(20, 2))
    parsed_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("Source", backref="smartlab_stocks")

    def __repr__(self):
        return f"<SmartlabStock(id={self.id}, ticker='{self.ticker}', name='{self.name}')>"

