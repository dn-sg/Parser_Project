"""
Парсер для раздела дивидендов сайта Dohod.ru
"""
from .base_parser import BaseParser
from bs4 import BeautifulSoup
from typing import List, Dict
import re
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)
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

        soup = BeautifulSoup(html, "html.parser")
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
                logger.error("Таблица с дивидендами не найдена")
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
                    record_date = self._parse_date(record_date_raw)

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
                    continue

        except Exception as e:
            logger.error(f"Критическая ошибка парсинга Dohod: {e}", exc_info=True)
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

    def _parse_date(self, text: str):
        """Конвертация DD.MM.YYYY -> Python date object"""
        if not text:
            return None
        # Проверка паттерна
        if not re.match(r'\d{2}\.\d{2}\.\d{4}', text):
            return None
        try:
            return datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return None

    def save_to_db(self, data: List[Dict]) -> None:
        """Сохранение данных в БД"""
        if not data:
            logger.warning("Нет данных для сохранения в БД.")
            return

        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # 1. Получаем ID источника
            cursor.execute("SELECT id FROM source WHERE name = 'Dohod' OR name = 'dohod.ru' LIMIT 1;")
            source_row = cursor.fetchone()

            if not source_row:
                logger.error("Источник 'Dohod' не найден в БД. Проверь таблицу source.")
                return

            source_id = source_row[0]

            # 2. Вставка данных
            # Предполагаем, что таблица называется dohod_divs
            insert_query = """
                INSERT INTO dohod_divs (
                    source_id, ticker, company_name, sector, period, 
                    payment_per_share, currency, yield_percent, 
                    record_date_estimate, capitalization_mln_rub, dsi
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """

            for item in data:
                cursor.execute(insert_query, (
                    source_id,
                    item['ticker'],
                    item['company_name'],
                    item['sector'],
                    item['period'],
                    item['payment_per_share'],
                    item['currency'],
                    item['yield_percent'],
                    item['record_date_estimate'],  # драйвер сам преобразует date -> SQL DATE
                    item['capitalization_mln_rub'],
                    item['dsi']
                ))

            conn.commit()
            logger.info(f"Успешно сохранено {len(data)} записей дивидендов.")

        except Exception as e:
            logger.error(f"Ошибка сохранения в БД: {e}", exc_info=True)
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()


def run_dohod_parser():
    """Функция запуска"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        parser = DohodParser()
        logger.info("Начинаем парсинг Dohod.ru...")

        data = parser.parse()

        if data:
            logger.info(f"Спарсено {len(data)} записей.")

            # Сохраняем в БД
            parser.save_to_db(data)

            # # Сохраняем в JSON (для дебага, сериализуем даты как строки)
            # def date_handler(obj):
            #     if hasattr(obj, 'isoformat'):
            #         return obj.isoformat()
            #     return obj
            #
            # with open("dohod_divs.json", "w", encoding="utf-8") as f:
            #     json.dump(data, f, ensure_ascii=False, indent=2, default=date_handler)

            logger.info("Готово.")
        else:
            logger.warning("Пустой результат парсинга.")

    except Exception as e:
        logger.error(f"Ошибка запуска: {e}", exc_info=True)


if __name__ == "__main__":
    run_dohod_parser()
