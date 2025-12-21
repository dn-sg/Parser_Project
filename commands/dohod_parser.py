"""
Парсер для раздела дивидендов сайта Dohod.ru
Применяет SOLID принципы
"""
from bs4 import BeautifulSoup
from typing import List, Dict
import re
import logging
from datetime import datetime
from .base_parser import BaseParser
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from adapters.http_client import IHttpClient

logger = logging.getLogger(__name__)


class DohodParser(BaseParser):
    """
    Парсер страницы дивидендов Dohod.ru
    URL: https://www.dohod.ru/ik/analytics/dividend
    """
    
    def __init__(self, http_client: IHttpClient = None):
        """Инициализация парсера Dohod"""
        super().__init__("https://www.dohod.ru/ik/analytics/dividend", http_client)
    
    def parse(self) -> List[Dict]:
        """
        Парсинг таблицы с дивидендами.
        
        Returns:
            Список словарей, где каждый словарь — это строка таблицы.
        """
        html = self.fetch_html()
        soup = BeautifulSoup(html, "html.parser")
        
        table = soup.find('table', {'id': 'table-dividend'})
        if not table:
            tables = soup.find_all('table')
            for t in tables:
                if t.find('th', string=re.compile('Акция|Ticker|Symbol')):
                    table = t
                    break
        
        if not table:
            logger.error("Таблица с дивидендами не найдена")
            return []
        
        rows = table.find_all('tr')
        data_rows = [row for row in rows if not row.find('th') and 'filter-row' not in row.get('class', [])]
        
        data_list = []
        for row in data_rows:
            cells = row.find_all('td')
            if len(cells) < 8:
                continue
            
            try:
                item = self._parse_row(cells)
                if item:
                    data_list.append(item)
            except Exception as e:
                logger.warning(f"Ошибка при парсинге строки: {e}")
                continue
        
        return data_list
    
    def _parse_row(self, cells: List) -> Dict:
        """Парсинг одной строки таблицы"""
        # Извлечение данных по колонкам
        name_link = cells[0].find('a')
        if not name_link:
            name_link = cells[1].find('a')
        
        ticker = ""
        company_name = name_link.get_text(strip=True) if name_link else ""
        
        if name_link and 'href' in name_link.attrs:
            href_parts = name_link['href'].split('/')
            if href_parts:
                ticker = href_parts[-1].upper()
        
        sector = self._get_text(cells, 2)
        period = self._get_text(cells, 3)
        payment_val = self._parse_float(self._get_text(cells, 4))
        currency = self._get_text(cells, 5)
        yield_percent = self._parse_percent(self._get_text(cells, 6))
        record_date_raw = self._get_text(cells, 8)
        record_date = self._parse_date(record_date_raw)
        capitalization = self._parse_float(self._get_text(cells, 9).replace(' ', ''))
        dsi_index = self._parse_float(self._get_text(cells, 10))
        
        return {
            "ticker": ticker,
            "company_name": company_name,
            "sector": sector,
            "period": period,
            "payment_per_share": payment_val,
            "currency": currency,
            "yield_percent": yield_percent,
            "record_date_estimate": record_date,
            "capitalization_mln_rub": capitalization,
            "dsi": dsi_index
        }
    
    def _get_text(self, cells, index: int) -> str:
        """Безопасное получение текста из ячейки"""
        if index < len(cells):
            return cells[index].get_text(strip=True)
        return ""
    
    def _parse_float(self, text: str) -> float:
        """Преобразование строки в float"""
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
    
    def _parse_date(self, text: str):
        """Конвертация DD.MM.YYYY -> Python date object"""
        if not text:
            return None
        if not re.match(r'\d{2}\.\d{2}\.\d{4}', text):
            return None
        try:
            return datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return None

