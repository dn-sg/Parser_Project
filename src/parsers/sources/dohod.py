"""
Парсер для раздела дивидендов сайта Dohod.ru
"""
from .base_parser import BaseParser
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
import logging
from datetime import datetime
import json


logger = logging.getLogger(__name__)

CURRENCY_RE = re.compile(r"^(RUB|USD|EUR|CNY|HKD|GBP)$", re.IGNORECASE)

class DohodParser(BaseParser):
    def __init__(self):
        super().__init__("https://www.dohod.ru/ik/analytics/dividend")

    def parse(self) -> List[Dict]:
        html = self.fetch_html()
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")

        # 1) таблица по id, иначе fallback: первая table, где есть th "Ticker"
        table = soup.find("table", {"id": "table-dividend"})
        if not table:
            for t in soup.find_all("table"):
                th_texts = [th.get_text(" ", strip=True).lower() for th in t.find_all("th")]
                if any("ticker" in x for x in th_texts):
                    table = t
                    break

        if not table:
            logger.error("Таблица table-dividend не найдена")
            return []

        # 2) определяем "тело" таблицы
        tbody = table.find("tbody") or table

        # 3) если есть строка заголовков (th) внутри table (без thead) — пропустим её
        #    (в тестах она идёт первой строкой)
        data_rows = tbody.find_all("tr")
        if data_rows and data_rows[0].find_all("th"):
            data_rows = data_rows[1:]

        data_list: List[Dict] = []

        for row in data_rows:
            # пропускаем filter-row из теста
            cls = row.get("class") or []
            if "filter-row" in cls:
                continue

            cells = row.find_all("td")
            # в тестах "правильная" строка = 11 td
            if len(cells) < 11:
                continue

            # Фиксированная схема из тестов:
            # 0 ticker/link, 1 name, 2 sector, 3 period, 4 payment, 5 currency,
            # 6 yield, 8 record date, 9 cap, 10 dsi
            ticker_cell = cells[0]
            name_cell = cells[1] if len(cells) > 1 else cells[0]

            link = ticker_cell.find("a", href=True) or name_cell.find("a", href=True)
            company_name = (name_cell.get_text(" ", strip=True) or ticker_cell.get_text(" ", strip=True))

            ticker = ""
            if link and link.get("href"):
                ticker = link["href"].rstrip("/").split("/")[-1].upper()

            sector = cells[2].get_text(" ", strip=True)
            period = cells[3].get_text(" ", strip=True)

            payment_val = self._parse_float(cells[4].get_text(" ", strip=True))

            currency = cells[5].get_text(" ", strip=True).upper()
            if not CURRENCY_RE.match(currency):
                currency = ""

            yield_percent = self._parse_percent(cells[6].get_text(" ", strip=True))

            record_date = self._parse_date(cells[8].get_text(" ", strip=True))

            capitalization = self._parse_float(cells[9].get_text(" ", strip=True))
            dsi_index = self._parse_float(cells[10].get_text(" ", strip=True))

            data_list.append(
                {
                    "ticker": ticker,
                    "company_name": company_name,
                    "sector": sector,
                    "period": period,
                    "payment_per_share": payment_val,
                    "currency": currency,
                    "yield_percent": yield_percent,
                    "record_date_estimate": record_date,
                    "capitalization_mln_rub": capitalization,
                    "dsi": dsi_index,
                }
            )

        return data_list

    def _parse_float(self, text: str) -> float:
        # тесты хотят 0.0 на мусор
        if text is None:
            return 0.0
        t = text.strip()
        if not t or t.lower() in {"n/a", "na", "-", "—"}:
            return 0.0

        m = re.search(r"-?\d+(?:[ \u00A0\u202F]\d{3})*(?:[.,]\d+)?", t.replace("−", "-"))
        if not m:
            return 0.0

        num = (
            m.group(0)
            .replace(" ", "")
            .replace("\u00A0", "")
            .replace("\u202F", "")
            .replace(",", ".")
        )
        try:
            return float(num)
        except ValueError:
            return 0.0

    def _parse_percent(self, text: str) -> float:
        if text is None:
            return 0.0
        t = text.strip().replace("%", "")
        if not t or t.lower() in {"n/a", "na", "-", "—"}:
            return 0.0

        m = re.search(r"-?\d+(?:[.,]\d+)?", t.replace("−", "-"))
        if not m:
            return 0.0

        num = m.group(0).replace(",", ".")
        try:
            return float(num)
        except ValueError:
            return 0.0

    def _parse_date(self, text: str):
        if not text:
            return None
        if text.strip().lower() in {"n/a", "na", "-", "—"}:
            return None

        m = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", text)
        if not m:
            return None
        try:
            return datetime.strptime(m.group(0), "%d.%m.%Y").date()
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

            # Сохраняем в JSON (для дебага, сериализуем даты как строки)
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
