"""
Парсер для сайта SmartLab - акции
Применяет SOLID принципы
"""
from bs4 import BeautifulSoup, Tag
from typing import List, Dict
import logging
from .base_parser import BaseParser
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from adapters.http_client import IHttpClient

logger = logging.getLogger(__name__)

# Шаблон данных компании
COMPANY_TEMPLATE: Dict[str, str] = {
    "name": "No information!",
    "ticker": "No information!",
    "last price, rub": "No information!",
    "price change": "No information!",
    "volume, mln rub": "No information!",
    "change in one week": "No information!",
    "change in one month": "No information!",
    "change in year to date": "No information!",
    "change in twelve month": "No information!",
    "capitalization, bln rub": "No information!",
    "capitalization, bln usd": "No information!",
}


class SmartlabParser(BaseParser):
    """Парсер для сайта SmartLab - акции"""
    
    def __init__(self, url: str = "https://smart-lab.ru/q/shares/", http_client: IHttpClient = None):
        """Инициализация парсера SmartLab"""
        super().__init__(url, http_client)
    
    def parse(self) -> List[Dict]:
        """
        Парсинг таблицы акций со страницы Smartlab
        
        Returns:
            Список словарей с данными компаний
        """
        html = self.fetch_html()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Поиск основной таблицы
        main_table = soup.find("div", class_="main__table")
        if not main_table:
            logger.error("Не найден контейнер таблицы (main__table)")
            return []
        
        table = main_table.find("table")
        if not table:
            logger.error("Не найдена таблица внутри контейнера")
            return []
        
        rows = table.find_all("tr")
        if not rows:
            logger.warning("Таблица пуста - не найдено строк")
            return []
        
        stocks = []
        # Пропускаем заголовок (первую строку)
        for row in rows[1:]:
            try:
                company_data = self._parse_row(row)
                if company_data:
                    stocks.append(company_data)
            except Exception as e:
                logger.warning(f"Ошибка при обработке строки таблицы: {e}")
                continue
        
        logger.info(f"Успешно спарсено {len(stocks)} компаний")
        return stocks
    
    def _parse_row(self, row: Tag) -> Dict[str, str]:
        """Парсинг одной строки таблицы"""
        company_data = COMPANY_TEMPLATE.copy()
        
        company_data["name"] = self._extract_cell_text(row, "td", "trades-table__name", link_text=True)
        company_data["ticker"] = self._extract_cell_text(row, "td", "trades-table__ticker")
        company_data["last price, rub"] = self._extract_cell_text(row, "td", "trades-table__price")
        company_data["price change"] = self._extract_cell_text(row, "td", "trades-table__change-per")
        company_data["volume, mln rub"] = self._extract_cell_text(row, "td", "trades-table__volume")
        company_data["change in one week"] = self._extract_cell_text(row, "td", "trades-table__week")
        company_data["change in one month"] = self._extract_cell_text(row, "td", "trades-table__month")
        company_data["change in year to date"] = self._extract_cell_text(row, "td", "trades-table__first")
        company_data["change in twelve month"] = self._extract_cell_text(row, "td", "trades-table__year")
        company_data["capitalization, bln rub"] = self._extract_cell_text(row, "td", "trades-table__rub")
        company_data["capitalization, bln usd"] = self._extract_cell_text(row, "td", "trades-table__usd")
        
        return company_data
    
    def _extract_cell_text(self, row: Tag, tag_name: str, class_name: str = None, link_text: bool = False) -> str:
        """
        Безопасное извлечение текста из ячейки таблицы
        
        Args:
            row: Строка таблицы
            tag_name: Название тега для поиска
            class_name: Название класса для поиска (опционально)
            link_text: Если True, ищет текст внутри ссылки в ячейке
            
        Returns:
            Текст из ячейки или "No information!" если ячейка не найдена
        """
        try:
            cell = row.find(tag_name, class_=class_name) if class_name else row.find(tag_name)
            if not cell:
                return "No information!"
            
            if link_text:
                link = cell.find("a")
                if link:
                    return link.get_text(strip=True)
                return "No information!"
            
            return cell.get_text(strip=True)
        except (AttributeError, TypeError) as e:
            logger.warning(f"Ошибка при извлечении текста из ячейки: {e}")
            return "No information!"

