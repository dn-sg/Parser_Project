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
from src.database import Source


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

        # таблица по id
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

        # определяю тело таблицы
        tbody = table.find("tbody") or table

        data_rows = tbody.find_all("tr")
        if data_rows and data_rows[0].find_all("th"):
            data_rows = data_rows[1:]

        data_list: List[Dict] = []

        for row in data_rows:
            cls = row.get("class") or []
            if "filter-row" in cls:
                continue

            cells = row.find_all("td")
            if len(cells) < 11:
                continue

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
        """Сохранение данных в БД через SQLAlchemy"""
        if not data:
            logger.warning("Нет данных для сохранения в БД.")
            return

        session = None
        try:
            session = self._get_db_session()
            # Получаю источник
            source = session.query(Source).filter(
                (Source.name == "Dohod") | (Source.name == "dohod.ru")
            ).first()
            
            if not source:
                logger.error("Источник 'Dohod' не найден в БД. Проверь таблицу source.")
                return

            # Импортирую модель
            from src.database import DohodDiv
            from decimal import Decimal

            # Вставляю данные
            for item in data:
                div = DohodDiv(
                    source_id=source.id,
                    ticker=item.get('ticker'),
                    company_name=item.get('company_name'),
                    sector=item.get('sector'),
                    period=item.get('period'),
                    payment_per_share=Decimal(str(item.get('payment_per_share', 0))),
                    currency=item.get('currency'),
                    yield_percent=Decimal(str(item.get('yield_percent', 0))),
                    record_date_estimate=item.get('record_date_estimate'),
                    capitalization_mln_rub=Decimal(str(item.get('capitalization_mln_rub', 0))),
                    dsi=Decimal(str(item.get('dsi', 0))),
                )
                session.add(div)

            session.commit()
            logger.info(f"Успешно сохранено {len(data)} записей дивидендов.")

        except Exception as e:
            logger.error(f"Ошибка сохранения в БД: {e}", exc_info=True)
            if session:
                session.rollback()
        finally:
            if session:
                session.close()


def run_dohod_parser():
    """Функция запуска"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        parser = DohodParser()
        logger.info("Начинаем парсинг Dohod.ru...")

        data = parser.parse()

        if data:
            logger.info(f"Спарсено {len(data)} записей.")

            # Сохраняю в БД
            parser.save_to_db(data)

            logger.info("Готово.")
        else:
            logger.warning("Пустой результат парсинга.")

    except Exception as e:
        logger.error(f"Ошибка запуска: {e}", exc_info=True)


if __name__ == "__main__":
    run_dohod_parser()
