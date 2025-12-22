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
        table = soup.find("table", {"id": "table-dividend"})
        if not table:
            logger.error("Таблица table-dividend не найдена")
            return []

        # 1) Заголовки -> индексы колонок (учитывая скрытые/тех. th)
        headers = [th.get_text(" ", strip=True) for th in table.select("thead th")]
        if not headers:
            logger.error("Не найдены заголовки таблицы (thead th)")
            return []

        def find_col(patterns: List[str]) -> Optional[int]:
            for i, h in enumerate(headers):
                hh = (h or "").lower()
                for p in patterns:
                    if re.search(p, hh):
                        return i
            return None

        col_name = find_col([r"\bакция\b"])
        col_sector = find_col([r"\bсектор\b"])
        col_period = find_col([r"\bпериод\b"])
        col_payment = find_col([r"\bвыплата\b"])
        col_yield = find_col([r"\bдоходност"])
        col_record_date = find_col([r"\bдата\b.*\bреестр", r"\bзакрытия\b"])
        col_cap = find_col([r"\bкапитализац"])
        col_dsi = find_col([r"\bdsi\b"])

        required = {
            "name": col_name,
            "sector": col_sector,
            "period": col_period,
            "payment": col_payment,
            "yield": col_yield,
            "record_date": col_record_date,
            "cap": col_cap,
            "dsi": col_dsi,
        }
        if any(v is None for v in required.values()):
            logger.error(f"Не удалось сопоставить колонки по заголовкам: {required}")
            return []

        # Валюта обычно стоит сразу после "Выплата..."
        col_currency = None
        if col_payment is not None and col_payment + 1 < len(headers):
            col_currency = col_payment + 1

        # ... после расчёта col_* и required ...

        max_needed_idx = max(col_name, col_sector, col_period, col_payment, col_yield, col_record_date, col_cap,
                             col_dsi)

        data_list: List[Dict] = []
        tbody = table.find("tbody") or table

        for row in tbody.find_all("tr"):
            cells = row.find_all("td")  # <- без recursive=False, так надёжнее

            # пропускаем “не-данные”
            if len(cells) <= max_needed_idx:
                continue

            name_cell = cells[col_name]
            link = name_cell.find("a", href=True)
            company_name = link.get_text(strip=True) if link else name_cell.get_text(" ", strip=True)

            ticker = ""
            if link and link.get("href"):
                ticker = link["href"].rstrip("/").split("/")[-1].upper()

            sector = cells[col_sector].get_text(" ", strip=True)
            period = cells[col_period].get_text(" ", strip=True)

            payment_raw = cells[col_payment].get_text(" ", strip=True)
            payment_val = self._parse_float(payment_raw)

            # Валюта: ищем в следующих 1–3 ячейках после выплаты (на сайте бывает “пустая” колонка между ними)
            currency = ""
            for j in range(col_payment + 1, min(col_payment + 4, len(cells))):
                cur = cells[j].get_text(" ", strip=True).upper()
                if CURRENCY_RE.match(cur):
                    currency = cur
                    break

            yield_raw = cells[col_yield].get_text(" ", strip=True)
            yield_percent = self._parse_percent(yield_raw)

            record_date_raw = cells[col_record_date].get_text(" ", strip=True)
            record_date = self._parse_date(record_date_raw)

            cap_raw = cells[col_cap].get_text(" ", strip=True)
            capitalization = self._parse_float(cap_raw)

            dsi_raw = cells[col_dsi].get_text(" ", strip=True)
            dsi_index = self._parse_float(dsi_raw)

            data_list.append({
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
            })

        return data_list

    def _parse_float(self, text: str) -> Optional[float]:
        if not text:
            return None
        t = text.strip().lower()
        if t in {"n/a", "na", "-", "—"}:
            return None

        # берём первое “похожее на число” в строке, чтобы не ломаться от иконок/пометок
        m = re.search(r"-?\d+(?:[ \u00A0\u202F]\d{3})*(?:[.,]\d+)?", text.replace("−", "-"))
        if not m:
            return None

        num = m.group(0)
        num = num.replace(" ", "").replace("\u00A0", "").replace("\u202F", "").replace(",", ".")
        try:
            return float(num)
        except ValueError:
            return None

    def _parse_percent(self, text: str) -> Optional[float]:
        if not text:
            return None
        t = text.strip().lower()
        if t in {"n/a", "na", "-", "—"}:
            return None

        m = re.search(r"-?\d+(?:[.,]\d+)?", text.replace("−", "-"))
        if not m:
            return None

        num = m.group(0).replace(",", ".")
        try:
            return float(num)
        except ValueError:
            return None

    def _parse_date(self, text: str):
        if not text:
            return None
        # “n/a” и т.п.
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
