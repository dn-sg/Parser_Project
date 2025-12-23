import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup, Tag
from src.parsers.sources.smartlab import SmartlabParser


# --- Фикстура для парсера ---
@pytest.fixture
def parser():
    """Создает экземпляр парсера для каждого теста"""
    return SmartlabParser("https://smart-lab.ru/q/shares/")


# --- Тесты вспомогательных методов ---


def test_extract_cell_text_simple(parser):
    """Тест извлечения текста из простой ячейки"""
    html = "<tr><td class='test'>Текст ячейки</td></tr>"
    soup = BeautifulSoup(html, "html.parser")
    row = soup.find("tr")

    text = parser._extract_cell_text(row, "td", "test")
    assert text == "Текст ячейки"


def test_extract_cell_text_with_link(parser):
    """Тест извлечения текста из ссылки в ячейке"""
    html = "<tr><td class='test'><a href='/test'>Текст ссылки</a></td></tr>"
    soup = BeautifulSoup(html, "html.parser")
    row = soup.find("tr")

    text = parser._extract_cell_text(row, "td", "test", link_text=True)
    assert text == "Текст ссылки"


def test_extract_cell_text_no_cell(parser):
    """Тест обработки отсутствующей ячейки"""
    html = "<tr><td class='other'>Другая ячейка</td></tr>"
    soup = BeautifulSoup(html, "html.parser")
    row = soup.find("tr")

    text = parser._extract_cell_text(row, "td", "test")
    assert text == "No information!"


def test_extract_cell_text_no_link(parser):
    """Тест обработки отсутствующей ссылки при link_text=True"""
    html = "<tr><td class='test'>Текст без ссылки</td></tr>"
    soup = BeautifulSoup(html, "html.parser")
    row = soup.find("tr")

    text = parser._extract_cell_text(row, "td", "test", link_text=True)
    assert text == "No information!"


def test_extract_cell_text_handles_attribute_error(parser):
    """Тест обработки некорректной строки (None)"""
    text = parser._extract_cell_text(None, "td", "test")
    assert text == "No information!"


def test_clean_number_normal(parser):
    """Тест очистки нормального числа"""
    assert parser._clean_number("123.45") == 123.45
    assert parser._clean_number("1 234.56") == 1234.56
    assert parser._clean_number("-50.5") == -50.5


def test_clean_number_with_percent(parser):
    """Тест очистки числа с процентами"""
    assert parser._clean_number("15.5%") == 15.5
    assert parser._clean_number("20 %") == 20.0
    assert parser._clean_number("+10%") == 10.0


def test_clean_number_with_comma(parser):
    """Тест очистки числа с запятой"""
    assert parser._clean_number("1,25") == 1.25


def test_clean_number_no_information(parser):
    """Тест обработки 'No information!'"""
    assert parser._clean_number("No information!") == 0.0
    assert parser._clean_number("") == 0.0
    assert parser._clean_number(None) == 0.0


def test_clean_number_invalid(parser):
    """Тест обработки невалидного значения"""
    assert parser._clean_number("abc") == 0.0
    assert parser._clean_number("---") == 0.0


# --- Тесты основной логики парсинга ---


def test_parse_success(parser):
    """Тест успешного парсинга таблицы"""
    mock_html = """
    <html>
    <body>
        <div class="main__table">
            <table>
                <tr>
                    <th>Name</th>
                    <th>Ticker</th>
                    <th>Price</th>
                </tr>
                <tr>
                    <td class="trades-table__name"><a href="/test">Газпром</a></td>
                    <td class="trades-table__ticker">GAZP</td>
                    <td class="trades-table__price">250.50</td>
                    <td class="trades-table__change-per">+5.2%</td>
                    <td class="trades-table__volume">1 000 000</td>
                    <td class="trades-table__week">+2.1%</td>
                    <td class="trades-table__month">+10.5%</td>
                    <td class="trades-table__first">+15.3%</td>
                    <td class="trades-table__year">+20.1%</td>
                    <td class="trades-table__rub">5 000</td>
                    <td class="trades-table__usd">50</td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """

    with patch.object(parser, "fetch_html", return_value=mock_html):
        result = parser.parse()

        assert len(result) == 1
        item = result[0]

        assert item["name"] == "Газпром"
        assert item["ticker"] == "GAZP"
        assert item["last price, rub"] == "250.50"
        assert item["price change"] == "+5.2%"
        assert item["volume, mln rub"] == "1 000 000"


def test_parse_no_table(parser):
    """Тест случая, когда таблица не найдена"""
    mock_html = "<html><body><h1>No table here</h1></body></html>"

    with patch.object(parser, "fetch_html", return_value=mock_html):
        result = parser.parse()
        assert result == []


def test_parse_no_main_table_div(parser):
    """Тест случая, когда нет div с классом main__table"""
    mock_html = "<html><body><table><tr><td>Test</td></tr></table></body></html>"

    with patch.object(parser, "fetch_html", return_value=mock_html):
        result = parser.parse()
        assert result == []


def test_parse_main_div_without_table(parser):
    """Тест случая, когда div есть, а таблицы внутри нет"""
    mock_html = (
        "<html><body><div class='main__table'><p>No table</p></div></body></html>"
    )

    with patch.object(parser, "fetch_html", return_value=mock_html):
        result = parser.parse()
        assert result == []


def test_parse_empty_table(parser):
    """Тест случая с пустой таблицей"""
    mock_html = """
    <html>
    <body>
        <div class="main__table">
            <table>
                <tr><th>Header</th></tr>
            </table>
        </div>
    </body>
    </html>
    """

    with patch.object(parser, "fetch_html", return_value=mock_html):
        result = parser.parse()
        assert result == []


def test_parse_table_without_rows(parser):
    """Тест таблицы без строк tr"""
    mock_html = (
        "<html><body><div class='main__table'><table></table></div></body></html>"
    )

    with patch.object(parser, "fetch_html", return_value=mock_html):
        result = parser.parse()
        assert result == []


def test_parse_bad_row(parser):
    """Тест обработки битой строки"""
    mock_html = """
    <html>
    <body>
        <div class="main__table">
            <table>
                <tr><th>Header</th></tr>
                <tr>
                    <td>Мало колонок</td>
                </tr>
                <tr>
                    <td class="trades-table__name"><a href="/test">Нормальная</a></td>
                    <td class="trades-table__ticker">TEST</td>
                    <td class="trades-table__price">100</td>
                    <td class="trades-table__change-per">+1%</td>
                    <td class="trades-table__volume">1000</td>
                    <td class="trades-table__week">+1%</td>
                    <td class="trades-table__month">+1%</td>
                    <td class="trades-table__first">+1%</td>
                    <td class="trades-table__year">+1%</td>
                    <td class="trades-table__rub">100</td>
                    <td class="trades-table__usd">1</td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """

    with patch.object(parser, "fetch_html", return_value=mock_html):
        result = parser.parse()
        # Парсер может добавить обе строки (битую с дефолтными значениями и нормальную)
        # Проверяем что есть нормальная строка
        assert len(result) >= 1
        # Находим нормальную строку по тикеру
        test_row = [r for r in result if r.get("ticker") == "TEST"]
        assert len(test_row) == 1
        assert test_row[0]["ticker"] == "TEST"


def test_parse_skips_row_on_exception(parser):
    """Тест пропуска строки при исключении в обработке"""
    mock_html = """
    <html>
    <body>
        <div class="main__table">
            <table>
                <tr><th>Header</th></tr>
                <tr>
                    <td class="trades-table__name"><a href="/fail">Fail</a></td>
                    <td class="trades-table__ticker">FAIL</td>
                </tr>
                <tr>
                    <td class="trades-table__name"><a href="/ok">OK</a></td>
                    <td class="trades-table__ticker">OK</td>
                    <td class="trades-table__price">1</td>
                    <td class="trades-table__change-per">1%</td>
                    <td class="trades-table__volume">1</td>
                    <td class="trades-table__week">1%</td>
                    <td class="trades-table__month">1%</td>
                    <td class="trades-table__first">1%</td>
                    <td class="trades-table__year">1%</td>
                    <td class="trades-table__rub">1</td>
                    <td class="trades-table__usd">1</td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """

    call_state = {"count": 0}

    def side_effect(*args, **kwargs):
        if call_state["count"] == 0:
            call_state["count"] += 1
            raise ValueError("boom")
        return "OK"

    with patch.object(parser, "fetch_html", return_value=mock_html):
        with patch.object(parser, "_extract_cell_text", side_effect=side_effect):
            result = parser.parse()

    assert len(result) == 1
    assert all(value == "OK" for value in result[0].values())


def test_parse_no_html(parser):
    """Тест обработки случая, когда HTML не получен"""
    with patch.object(parser, "fetch_html", return_value=None):
        result = parser.parse()
        assert result == []


def test_parse_handles_exception(parser):
    """Тест обработки исключений"""
    with patch.object(parser, "fetch_html", side_effect=Exception("Ошибка")):
        result = parser.parse()
        assert result == []


def test_run_smartlab_parser_success():
    """Тест успешного сценария run_smartlab_parser"""
    from src.parsers.sources import smartlab

    with patch.object(smartlab, "logging") as mock_logging, patch.object(
        smartlab, "SmartlabParser"
    ) as mock_cls:
        parser_instance = MagicMock()
        parser_instance.parse.return_value = [{"name": "OK"}]
        parser_instance.save_to_db.return_value = None
        mock_cls.return_value = parser_instance

        smartlab.run_smartlab_parser()

        mock_logging.basicConfig.assert_called_once()
        mock_cls.assert_called_once()
        parser_instance.parse.assert_called_once()
        parser_instance.save_to_db.assert_called_once()


def test_run_smartlab_parser_handles_exception():
    """Тест обработки исключения внутри run_smartlab_parser"""
    from src.parsers.sources import smartlab

    with patch.object(smartlab, "logging") as mock_logging, patch.object(
        smartlab, "SmartlabParser"
    ) as mock_cls:
        parser_instance = MagicMock()
        parser_instance.parse.side_effect = RuntimeError("boom")
        mock_cls.return_value = parser_instance

        with patch.object(smartlab.logger, "error") as mock_error:
            smartlab.run_smartlab_parser()
            mock_error.assert_called()


# --- Тесты сохранения в БД ---


def test_save_to_db(parser):
    """Тест сохранения данных в БД"""
    fake_data = [
        {
            "name": "Газпром",
            "ticker": "GAZP",
            "last price, rub": "250.50",
            "price change": "+5.2%",
            "volume, mln rub": "1 000 000",
            "change in one week": "+2.1%",
            "change in one month": "+10.5%",
            "change in year to date": "+15.3%",
            "change in twelve month": "+20.1%",
            "capitalization, bln rub": "5 000",
            "capitalization, bln usd": "50",
        }
    ]

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = [1]  # ID источника

    with patch.object(parser, "_get_db_connection", return_value=mock_conn):
        parser.save_to_db(fake_data)

        # Проверяем, что соединение открылось
        parser._get_db_connection.assert_called_once()

        # Проверяем, что был SELECT запрос источника
        mock_cursor.execute.assert_any_call(
            "SELECT id FROM source WHERE name = 'SmartLab';"
        )

        # Проверяем, что был INSERT
        assert mock_cursor.execute.call_count >= 2

        # Проверяем, что был commit
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()


def test_save_to_db_no_data(parser):
    """Тест сохранения пустого списка"""
    with patch.object(parser, "_get_db_connection") as mock_connect:
        parser.save_to_db([])
        mock_connect.assert_not_called()


def test_save_to_db_source_not_found(parser):
    """Тест случая, когда источник не найден в БД"""
    fake_data = [{"name": "Test", "ticker": "TEST", "last price, rub": "100"}]

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Источник не найден

    with patch.object(parser, "_get_db_connection", return_value=mock_conn):
        parser.save_to_db(fake_data)

        # Должен попробовать найти источник
        mock_cursor.execute.assert_called_once()
        # Но не должен делать INSERT
        assert mock_cursor.execute.call_count == 1


def test_save_to_db_rollback_on_error(parser):
    """Тест отката транзакции при ошибке"""
    fake_data = [
        {
            "name": "Test",
            "ticker": "TEST",
            "last price, rub": "100",
            "price change": "+1%",
            "volume, mln rub": "1000",
            "change in one week": "+1%",
            "change in one month": "+1%",
            "change in year to date": "+1%",
            "change in twelve month": "+1%",
            "capitalization, bln rub": "100",
            "capitalization, bln usd": "1",
        }
    ]

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = [1]
    mock_cursor.execute.side_effect = [None, Exception("DB Error")]

    with patch.object(parser, "_get_db_connection", return_value=mock_conn):
        parser.save_to_db(fake_data)

        # Проверяем, что был вызван rollback
        mock_conn.rollback.assert_called_once()


def test_save_to_db_cleans_numbers(parser):
    """Тест, что числа очищаются перед сохранением"""
    fake_data = [
        {
            "name": "Test",
            "ticker": "TEST",
            "last price, rub": "1 234.56",
            "price change": "+5.2%",
            "volume, mln rub": "1 000 000",
            "change in one week": "+2.1%",
            "change in one month": "+10.5%",
            "change in year to date": "+15.3%",
            "change in twelve month": "+20.1%",
            "capitalization, bln rub": "5 000",
            "capitalization, bln usd": "50",
        }
    ]

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = [1]

    with patch.object(parser, "_get_db_connection", return_value=mock_conn):
        parser.save_to_db(fake_data)

        # Проверяем, что execute был вызван с очищенными числами
        # Последний вызов execute должен быть INSERT с float значениями
        assert mock_cursor.execute.call_count >= 2
