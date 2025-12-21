"""
Репозитории для работы с данными через SQLAlchemy
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from models.source import Source
from models.rbc_news import RBCNews
from models.smartlab_stock import SmartlabStock
from models.dohod_dividend import DohodDividend


class Repository(ABC):
    """Базовый репозиторий"""
    
    def __init__(self, session: Session, source_name: str):
        self.session = session
        self.source_name = source_name
        self._source_id: Optional[int] = None
    
    @property
    def source_id(self) -> int:
        """Получение ID источника (ленивая загрузка)"""
        if self._source_id is None:
            source = self.session.query(Source).filter(Source.name == self.source_name).first()
            if not source:
                raise ValueError(f"Источник '{self.source_name}' не найден в таблице source")
            self._source_id = source.id
        return self._source_id
    
    @abstractmethod
    def save(self, data: List[Dict]) -> None:
        """Сохранение данных в БД"""
        pass


class RBCNewsRepository(Repository):
    """Репозиторий для новостей RBC"""
    
    def save(self, data: List[Dict]) -> None:
        """Сохранение новостей в БД"""
        if not data:
            return
        
        for item in data:
            # Проверяем, существует ли уже новость с таким URL
            existing = self.session.query(RBCNews).filter(
                RBCNews.url == item.get("url")
            ).first()
            
            if not existing:
                news = RBCNews(
                    source_id=self.source_id,
                    title=item.get("title"),
                    url=item.get("url"),
                    text=item.get("text")
                )
                self.session.add(news)


class SmartlabStockRepository(Repository):
    """Репозиторий для акций SmartLab"""
    
    def _clean_number(self, value: str) -> float:
        """Очистка строки и преобразование в float"""
        if not value or value == "No information!":
            return 0.0
        
        clean_val = value.replace(" ", "").replace("%", "").replace("+", "").replace(",", ".")
        try:
            return float(clean_val)
        except ValueError:
            return 0.0
    
    def save(self, data: List[Dict]) -> None:
        """Сохранение акций в БД"""
        if not data:
            return
        
        for item in data:
            stock = SmartlabStock(
                source_id=self.source_id,
                name=item.get("name"),
                ticker=item.get("ticker"),
                last_price_rub=self._clean_number(item.get("last price, rub", "0")),
                price_change_percent=self._clean_number(item.get("price change", "0")),
                volume_mln_rub=self._clean_number(item.get("volume, mln rub", "0")),
                change_week_percent=self._clean_number(item.get("change in one week", "0")),
                change_month_percent=self._clean_number(item.get("change in one month", "0")),
                change_ytd_percent=self._clean_number(item.get("change in year to date", "0")),
                change_year_percent=self._clean_number(item.get("change in twelve month", "0")),
                capitalization_bln_rub=self._clean_number(item.get("capitalization, bln rub", "0")),
                capitalization_bln_usd=self._clean_number(item.get("capitalization, bln usd", "0"))
            )
            self.session.add(stock)


class DohodDividendRepository(Repository):
    """Репозиторий для дивидендов Dohod"""
    
    def _parse_float(self, text: str) -> float:
        """Преобразование строки в float"""
        import re
        try:
            clean_text = re.sub(r'[^\d.,-]', '', text).replace(',', '.')
            return float(clean_text) if clean_text else 0.0
        except:
            return 0.0
    
    def _parse_percent(self, text: str) -> float:
        """Преобразование строки с процентом в float"""
        try:
            clean_text = text.replace('%', '').replace(',', '.').strip()
            return float(clean_text) if clean_text else 0.0
        except:
            return 0.0
    
    def save(self, data: List[Dict]) -> None:
        """Сохранение дивидендов в БД"""
        if not data:
            return
        
        for item in data:
            dividend = DohodDividend(
                source_id=self.source_id,
                ticker=item.get("ticker"),
                company_name=item.get("company_name"),
                sector=item.get("sector"),
                period=item.get("period"),
                payment_per_share=self._parse_float(str(item.get("payment_per_share", "0"))),
                currency=item.get("currency"),
                yield_percent=self._parse_percent(str(item.get("yield_percent", "0"))),
                record_date_estimate=item.get("record_date_estimate"),
                capitalization_mln_rub=self._parse_float(str(item.get("capitalization_mln_rub", "0"))),
                dsi=self._parse_float(str(item.get("dsi", "0")))
            )
            self.session.add(dividend)

