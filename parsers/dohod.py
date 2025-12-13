"""
Парсер для раздела дивидендов сайта Dohod.ru
"""
from .base_parser import BaseParser
from bs4 import BeautifulSoup
from typing import List, Dict
import re

class DohodParser(BaseParser):
    """
    Парсер страницы дивидендов Dohod.ru
    URL: https://www.dohod.ru/ik/analytics/dividend
    """

    def __init__(self):
        super().__init__("https://www.dohod.ru/ik/analytics/dividend")

    def parse(self) -> List[Dict]:
        """
        Парсинг таблицы с дивидендами.

        Returns:
            Список словарей, где каждый словарь — это строка таблицы.
        """
        html = self.fetch_html()
        if not html:
            return []

        soup = BeautifulSoup(html, 'lxml') # Используем lxml для скорости
        data_list = []

        try:
            # Ищем основную таблицу с данными
            # Часто она не имеет ID, поэтому ищем по характерным заголовкам или просто первую большую таблицу
            table = soup.find('table', {'id': 'table-dividend'})

            # Если по ID не нашли, ищем по классу content-table или просто первую таблицу
            if not table:
                tables = soup.find_all('table')
                for t in tables:
                    if t.find('th', text=re.compile('Акция|Ticker|Symbol')):
                        table = t
                        break

            if not table:
                print("Таблица с дивидендами не найдена")
                return []

            # Проходим по строкам тела таблицы
            # tbody может отсутствовать в верстке, поэтому ищем tr внутри table
            rows = table.find_all('tr')

            # Пропускаем заголовки (обычно первые 1-2 строки)
            # Фильтруем строки, которые являются заголовками или фильтрами
            data_rows = [row for row in rows if not row.find('th') and 'filter-row' not in row.get('class', [])]

            for row in data_rows:
                cells = row.find_all('td')

                # Пропускаем строки, где мало ячеек (например, разделители)
                if len(cells) < 8:
                    continue

                try:
                    # Извлечение данных по колонкам (индексы могут меняться, если сайт обновится)
                    # 0: Иконка (пропускаем)
                    # 1: Название акции (ссылка)
                    name_link = cells[0].find('a')
                    if not name_link:
                         # Иногда первая ячейка с плюсиком, тогда смещаемся
                         name_link = cells[1].find('a')

                    ticker = ""
                    company_name = name_link.get_text(strip=True) if name_link else ""

                    # Пытаемся вытащить тикер из ссылки (обычно .../dividend/ticker)
                    if name_link and 'href' in name_link.attrs:
                        href_parts = name_link['href'].split('/')
                        if href_parts:
                            ticker = href_parts[-1].upper()

                    # Собираем остальные поля, очищая от лишних пробелов и символов
                    sector = self._get_text(cells, 2)
                    period = self._get_text(cells, 3)

                    payment_val = self._parse_float(self._get_text(cells, 4))
                    currency = self._get_text(cells, 5)

                    yield_percent = self._parse_percent(self._get_text(cells, 6))

                    # Дата закрытия реестра
                    record_date_raw = self._get_text(cells, 8)
                    record_date = record_date_raw if self._is_valid_date(record_date_raw) else None

                    # Капитализация
                    capitalization = self._parse_float(self._get_text(cells, 9).replace(' ', ''))

                    dsi_index = self._parse_float(self._get_text(cells, 10))

                    item = {
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

                    data_list.append(item)

                except Exception as e:
                    # Логируем ошибку, но не роняем весь парсер из-за одной строки
                    # print(f"Ошибка парсинга строки {ticker}: {e}")
                    continue

        except Exception as e:
            print(f"Критическая ошибка парсинга Dohod: {e}")
            return []

        return data_list

    def _get_text(self, cells, index):
        """Безопасное получение текста из ячейки"""
        if index < len(cells):
            return cells[index].get_text(strip=True)
        return ""

    def _parse_float(self, text):
        """Преобразование строки в float"""
        try:
            clean_text = re.sub(r'[^\d.,-]', '', text).replace(',', '.')
            return float(clean_text) if clean_text else 0.0
        except:
            return 0.0

    def _parse_percent(self, text):
        """Преобразование строки с процентом в float"""
        try:
            clean_text = text.replace('%', '').replace(',', '.').strip()
            return float(clean_text) if clean_text else 0.0
        except:
            return 0.0

    def _is_valid_date(self, text):
        """Простая проверка, похоже ли на дату"""
        return bool(re.match(r'\d{2}\.\d{2}\.\d{4}', text))
