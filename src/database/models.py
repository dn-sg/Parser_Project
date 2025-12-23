"""
SQLAlchemy models for database tables
"""
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, 
    Numeric, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Source(Base):
    """Модель таблицы источников данных"""
    __tablename__ = "source"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    logs = relationship("Log", back_populates="source")
    rbc_news = relationship("RBCNews", back_populates="source")
    smartlab_stocks = relationship("SmartlabStock", back_populates="source")
    dohod_divs = relationship("DohodDiv", back_populates="source")


class Log(Base):
    """Модель таблицы логов выполнения парсеров"""
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("source.id"), nullable=False)
    celery_task_id = Column(String(255))
    status = Column(String(20))
    error_code = Column(String(50))
    error_message = Column(Text)
    items_parsed = Column(Integer, default=0)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    duration_seconds = Column(Integer)

    source = relationship("Source", back_populates="logs")
    
    __table_args__ = (
        Index("idx_logs_source_id", "source_id"),
    )


class RBCNews(Base):
    """Модель таблицы новостей RBC"""
    __tablename__ = "rbc_news"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("source.id"), nullable=False)
    title = Column(Text)
    url = Column(Text, unique=True)
    text = Column(Text)
    parsed_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("Source", back_populates="rbc_news")
    
    __table_args__ = (
        Index("idx_rbc_url", "url"),
    )


class SmartlabStock(Base):
    """Модель таблицы акций SmartLab"""
    __tablename__ = "smartlab_stocks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("source.id"), nullable=False)
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

    source = relationship("Source", back_populates="smartlab_stocks")
    
    __table_args__ = (
        Index("idx_smartlab_ticker", "ticker"),
    )


class DohodDiv(Base):
    """Модель таблицы дивидендов Dohod"""
    __tablename__ = "dohod_divs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("source.id"), nullable=False)
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

    source = relationship("Source", back_populates="dohod_divs")
    
    __table_args__ = (
        Index("idx_dohod_ticker", "ticker"),
    )
