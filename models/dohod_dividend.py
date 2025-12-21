"""
Модель дивидендов Dohod
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class DohodDividend(Base):
    """Модель дивиденда Dohod"""
    __tablename__ = 'dohod_divs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey('source.id'), nullable=False)
    ticker = Column(String(20))
    company_name = Column(String(255))
    sector = Column(String(100))
    period = Column(String(100))
    payment_per_share = Column(Numeric(10, 4))
    currency = Column(String(10))
    yield_percent = Column(Numeric(10, 2))
    record_date_estimate = Column(Date)
    capitalization_mln_rub = Column(Numeric(20, 2))
    dsi = Column(Numeric(10, 2))
    parsed_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("Source", backref="dohod_dividends")

    def __repr__(self):
        return f"<DohodDividend(id={self.id}, ticker='{self.ticker}', company='{self.company_name}')>"

