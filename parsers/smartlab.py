from .base_parser import BaseParser
from bs4 import BeautifulSoup, Tag
import logging
from typing import List, Dict

# Настройка логирования
logger: logging.Logger = logging.getLogger(__name__)

# Константы для селекторов HTML
class Selectors:
    """Селекторы для парсинга таблицы акций"""

    MAIN_TABLE: Dict[str, str] = {"name": "div", "class_": "main__table"}
    TABLE: Dict[str, str] = {"name": "table"}
    ROW: Dict[str, str] = {"name": "tr"}
    CELL_NAME: Dict[str, str] = {"name": "td", "class_": "trades-table__name"}
    CELL_TICKER: Dict[str, str] = {"name": "td", "class_": "trades-table__ticker"}
    CELL_PRICE: Dict[str, str] = {"name": "td", "class_": "trades-table__price"}
    CELL_CHANGE_PER: Dict[str, str] = {
        "name": "td",
        "class_": "trades-table__change-per",
    }
    CELL_VOLUME: Dict[str, str] = {"name": "td", "class_": "trades-table__volume"}
    CELL_WEEK: Dict[str, str] = {"name": "td", "class_": "trades-table__week"}
    CELL_MONTH: Dict[str, str] = {"name": "td", "class_": "trades-table__month"}
    CELL_YTD: Dict[str, str] = {"name": "td", "class_": "trades-table__first"}
    CELL_YEAR: Dict[str, str] = {"name": "td", "class_": "trades-table__year"}
    CELL_CAP_RUB: Dict[str, str] = {"name": "td", "class_": "trades-table__rub"}
    CELL_CAP_USD: Dict[str, str] = {"name": "td", "class_": "trades-table__usd"}
    LINK_NAME: Dict[str, str] = {"name": "a"}


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
    def __init__(self, url, headers=None) -> None:
        super().__init__(url=url, headers=headers)

    def _extract_cell_text(
        self, row: Tag, selector: Dict, link_text: bool = False
    ) -> str:
        """
        Безопасное извлечение текста из ячейки таблицы

        Args:
            row: Строка таблицы
            selector: Селектор для поиска ячейки
            link_text: Если True, ищет текст внутри ссылки в ячейке

        Returns:
            Текст из ячейки или "No information!" если ячейка не найдена
        """
        try:
            cell: Tag | None = row.find(**selector)
            if not cell:
                return "No information!"

            if link_text:
                link: Tag | None = cell.find(**Selectors.LINK_NAME)
                if link:
                    return link.get_text(strip=True)
                return "No information!"

            return cell.get_text(strip=True)
        except (AttributeError, TypeError) as e:
            logger.warning(msg=f"Ошибка при извлечении текста из ячейки: {e}")
            return "No information!"

    def parse(self) -> List[Dict]:
        """
        Парсинг таблицы акций со страницы Smartlab

        Returns:
            Список словарей с данными компаний
        """
        stocks: List[Dict[str, str]] = []

        try:
            html: str | None = self.fetch_html()
            if not html:
                logger.error(msg="Не удалось получить HTML содержимое")
                return []

            soup = BeautifulSoup(markup=html, features="html.parser")

            # Поиск основной таблицы
            main_table: Tag | None = soup.find(**Selectors.MAIN_TABLE)
            if not main_table:
                logger.error(msg="Не найден контейнер таблицы (main__table)")
                return []

            # Поиск самой таблицы
            table: Tag | None = main_table.find(**Selectors.TABLE)
            if not table:
                logger.error(msg="Не найдена таблица внутри контейнера")
                return []

            # Поиск строк таблицы
            rows: List[Tag] = table.find_all(**Selectors.ROW)
            if not rows:
                logger.warning(msg="Таблица пуста - не найдено строк")
                return []

            # Пропускаем заголовок (первую строку)
            for row in rows[1:]:
                try:
                    company_data: Dict[str, str] = COMPANY_TEMPLATE.copy()

                    # Название компании
                    company_data["name"] = self._extract_cell_text(
                        row=row, selector=Selectors.CELL_NAME, link_text=True
                    )

                    # Тикер
                    company_data["ticker"] = self._extract_cell_text(
                        row=row, selector=Selectors.CELL_TICKER
                    )

                    # Цена, последняя
                    company_data["last price, rub"] = self._extract_cell_text(
                        row=row, selector=Selectors.CELL_PRICE
                    )

                    # Изменение цены, %
                    company_data["price change"] = self._extract_cell_text(
                        row=row, selector=Selectors.CELL_CHANGE_PER
                    )

                    # Объём, млн руб
                    company_data["volume, mln rub"] = self._extract_cell_text(
                        row=row, selector=Selectors.CELL_VOLUME
                    )

                    # 1 неделя, %
                    company_data["change in one week"] = self._extract_cell_text(
                        row=row, selector=Selectors.CELL_WEEK
                    )

                    # 1 месяц, %
                    company_data["change in one month"] = self._extract_cell_text(
                        row=row, selector=Selectors.CELL_MONTH
                    )

                    # Year to date, %
                    company_data["change in year to date"] = self._extract_cell_text(
                        row=row, selector=Selectors.CELL_YTD
                    )

                    # 12 месяцев, %
                    company_data["change in twelve month"] = self._extract_cell_text(
                        row=row, selector=Selectors.CELL_YEAR
                    )

                    # Капитализация, млрд руб
                    company_data["capitalization, bln rub"] = self._extract_cell_text(
                        row=row, selector=Selectors.CELL_CAP_RUB
                    )

                    # Капитализация, млрд USD
                    company_data["capitalization, bln usd"] = self._extract_cell_text(
                        row=row, selector=Selectors.CELL_CAP_USD
                    )

                    stocks.append(company_data)

                except Exception as e:
                    logger.warning(msg=f"Ошибка при обработке строки таблицы: {e}")
                    continue

            logger.info(msg=f"Успешно спарсено {len(stocks)} компаний")
            return stocks

        except Exception as e:
            logger.error(msg=f"Критическая ошибка в методе parse(): {e}", exc_info=True)
            return []

    def _clean_number(self, value: str) -> float:
        """
        Очищает строку (удаляет пробелы, %, заменяет запятые) и возвращает float
        """
        if not value or value == "No information!":
            return 0.0

        # Убираем пробелы (разделители тысяч) и знаки % и +
        clean_val = value.replace(" ", "").replace("%", "").replace("+", "")
        # Если есть запятая, меняем на точку (хотя на smartlab обычно точки)
        clean_val = clean_val.replace(",", ".")

        try:
            return float(clean_val)
        except ValueError:
            return 0.0

    def save_to_db(self, data: List[Dict]) -> None:
        """Сохранение данных в БД"""
        if not data:
            logger.warning("Нет данных для сохранения в БД.")
            return

        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # 1. Получаем ID источника (SmartLab)
            cursor.execute("SELECT id FROM source WHERE name = 'SmartLab';")
            source_row = cursor.fetchone()

            if not source_row:
                logger.error("Ошибка: Источник 'SmartLab' не найден в таблице source.")
                return

            source_id = source_row[0]

            # 2. Вставляем данные
            insert_query = """
                INSERT INTO smartlab_stocks (
                    source_id, name, ticker, 
                    last_price_rub, price_change_percent, volume_mln_rub,
                    change_week_percent, change_month_percent, change_ytd_percent, change_year_percent,
                    capitalization_bln_rub, capitalization_bln_usd
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """

            for item in data:
                # Чистим данные перед вставкой
                params = (
                    source_id,
                    item.get("name"),
                    item.get("ticker"),
                    self._clean_number(item.get("last price, rub")),
                    self._clean_number(item.get("price change")),
                    self._clean_number(item.get("volume, mln rub")),
                    self._clean_number(item.get("change in one week")),
                    self._clean_number(item.get("change in one month")),
                    self._clean_number(item.get("change in year to date")),
                    self._clean_number(item.get("change in twelve month")),
                    self._clean_number(item.get("capitalization, bln rub")),
                    self._clean_number(item.get("capitalization, bln usd")),
                )
                cursor.execute(insert_query, params)

            conn.commit()
            logger.info(f"Успешно обработано {len(data)} записей для БД.")

        except Exception as e:
            logger.error(f"Ошибка при сохранении в БД: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()


def run_smartlab_parser():
    # Настройка логирования для консоли
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    URL = "https://smart-lab.ru/q/shares/"

    HEADERS: Dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15",
        "Accept": "text/html",
    }

    try:
        parser: SmartlabParser = SmartlabParser(url=URL, headers=HEADERS)

        # 1. Парсинг (получаем список словарей)
        logger.info("Начинаем парсинг...")
        data_list = parser.parse()

        if data_list:
            # 2. Сохранение в БД
            logger.info("Сохраняем данные в БД...")
            parser.save_to_db(data_list)

            # 3. Сохранение в JSON-файл
            logger.info("Сохраняем данные в smartlab_stocks.json...")
            json_str = parser.to_json(data_list)
            with open(file="smartlab_stocks.json", mode="w", encoding="utf-8") as file:
                file.write(json_str)

            logger.info("Все операции завершены успешно.")
        else:
            logger.warning("Нет данных для сохранения (парсинг вернул пустой список).")

    except Exception as e:
        logger.error(f"Ошибка при запуске парсера: {e}", exc_info=True)

if __name__ == "__main__":
    run_smartlab_parser()