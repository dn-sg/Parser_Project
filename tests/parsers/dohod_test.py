import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from src.parsers.sources.dohod import DohodParser  # Убедитесь, что импорт работает корректно


# --- Фикстура для парсера ---
@pytest.fixture
def parser():
    """Создает экземпляр парсера для каждого теста"""
    return DohodParser()


# --- Тесты вспомогательных методов (Unit tests) ---

def test_parse_float(parser):
    assert parser._parse_float("123,45") == 123.45
    assert parser._parse_float("1 234,56") == 1234.56
    assert parser._parse_float("-50.5") == -50.5
    assert parser._parse_float("abc") == 0.0
    assert parser._parse_float("") == 0.0


def test_parse_percent(parser):
    assert parser._parse_percent("15,5%") == 15.5
    assert parser._parse_percent("20 %") == 20.0
    assert parser._parse_percent("0") == 0.0
    assert parser._parse_percent("-") == 0.0


def test_parse_date(parser):
    assert parser._parse_date("25.12.2025") == date(2025, 12, 25)
    assert parser._parse_date("01.01.2024") == date(2024, 1, 1)
    assert parser._parse_date("invalid") is None
    assert parser._parse_date("") is None
    # Тест на неправильный формат
    assert parser._parse_date("2025-12-25") is None


# --- Тесты основной логики парсинга (Mocking HTML) ---

def test_parse_success(parser):
    """Тестируем парсинг корректного куска HTML"""

    # Эмулируем HTML, который отдаст сайт
    mock_html = """
    <html>
    <body>
        <table id="table-dividend">
            <thead>
                <tr><th>Ticker</th><th>Name</th></tr>
            </thead>
            <tbody>
                <!-- Строка заголовка фильтра, должна быть пропущена -->
                <tr class="filter-row"><td>...</td></tr>

                <!-- Реальная строка данных -->
                <tr>
                    <td><a href="/dividend/LKOH">ЛУКОЙЛ</a></td> <!-- 0 or 1 Name/Ticker -->
                    <td><a href="/dividend/LKOH">ЛУКОЙЛ</a></td> <!-- Дублируем для надежности поиска -->
                    <td>Нефтегаз</td>      <!-- 2 Sector -->
                    <td>2023 год</td>      <!-- 3 Period -->
                    <td>500,50</td>        <!-- 4 Payment -->
                    <td>RUB</td>           <!-- 5 Currency -->
                    <td>10,5%</td>         <!-- 6 Yield -->
                    <td>ignore</td>        <!-- 7 -->
                    <td>20.12.2025</td>    <!-- 8 Record Date -->
                    <td>1 000 000</td>     <!-- 9 Cap -->
                    <td>0,85</td>          <!-- 10 DSI -->
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """

    # Подменяем метод fetch_html, чтобы он не лез в интернет, а возвращал нашу строку
    with patch.object(parser, "fetch_html", return_value=mock_html):
        result = parser.parse()

        assert len(result) == 1
        item = result[0]

        assert item["ticker"] == "LKOH"
        assert item["company_name"] == "ЛУКОЙЛ"
        assert item["sector"] == "Нефтегаз"
        assert item["payment_per_share"] == 500.5
        assert item["yield_percent"] == 10.5
        assert item["record_date_estimate"] == date(2025, 12, 20)
        assert item["capitalization_mln_rub"] == 1000000.0
        assert item["dsi"] == 0.85


def test_parse_no_table(parser):
    """Тест случая, когда на странице нет нужной таблицы"""
    mock_html = "<html><body><h1>Access Denied</h1></body></html>"

    with patch.object(parser, 'fetch_html', return_value=mock_html):
        result = parser.parse()
        assert result == []


def test_parse_bad_row(parser):
    """Тест, что парсер не падает из-за одной битой строки"""
    mock_html = """
    <table id="table-dividend">
        <tr>
            <td>Мало колонок</td>
        </tr>
         <tr>
            <td><a href="/TEST">Норм</a></td>
            <td><a href="/TEST">Норм</a></td>
            <td>Сектор</td><td>Период</td><td>10</td><td>RUB</td><td>5%</td><td>-</td><td>01.01.2025</td><td>100</td><td>1</td>
        </tr>
    </table>
    """
    with patch.object(parser, "fetch_html", return_value=mock_html):
        result = parser.parse()
        assert len(result) == 1
        assert result[0]["ticker"] == "TEST"


# --- Тест сохранения в БД (Mocking Database) ---

def test_save_to_db(parser):
    """Проверяем, что метод вызывает SQL-запросы, но не пишем реально в БД"""

    # Подготовим фейковые данные
    fake_data = [{
        "ticker": "TEST",
        "company_name": "Test Co",
        "sector": "IT",
        "period": "Q1",
        "payment_per_share": 10.0,
        "currency": "RUB",
        "yield_percent": 5.0,
        "record_date_estimate": date(2025, 1, 1),
        "capitalization_mln_rub": 100.0,
        "dsi": 1.0
    }]

    # Создаем моки для соединения и курсора
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Мокаем результат SELECT id FROM source (возвращаем ID=1)
    mock_cursor.fetchone.return_value = [1]

    # Подменяем _get_db_connection в парсере
    with patch.object(parser, '_get_db_connection', return_value=mock_conn):
        parser.save_to_db(fake_data)

        # Проверяем, что соединение открылось
        parser._get_db_connection.assert_called_once()

        # Проверяем, что был SELECT запрос источника
        mock_cursor.execute.assert_any_call("SELECT id FROM source WHERE name = 'Dohod' OR name = 'dohod.ru' LIMIT 1;")

        # Проверяем, что был INSERT
        # (assert_called_with проверяет последний вызов, если их было много - используйте assert_any_call)
        assert mock_cursor.execute.call_count >= 2

        # Проверяем, что был commit
        mock_conn.commit.assert_called_once()
        # Проверяем, что закрыли соединение
        mock_conn.close.assert_called_once()


def test_save_to_db_no_data(parser):
    """Проверка выхода, если данных нет"""
    with patch.object(parser, '_get_db_connection') as mock_connect:
        parser.save_to_db([])
        mock_connect.assert_not_called()


def test_parse_fallback_table_search(parser):
    """Проверка поиска таблицы, если у нее нет ID, но есть нужные заголовки"""
    mock_html = """
    <html>
    <body>
        <!-- Таблица без ID, но с заголовком Ticker -->
        <table class="some-random-class">
            <tr><th>Ticker</th><th>Name</th></tr>
            <tr>
                <td><a href="/dividend/TEST">Test Co</a></td>
                <td>Test Co</td><td>Sec</td><td>Per</td><td>10</td><td>RUB</td><td>5%</td><td>-</td><td>01.01.2025</td><td>100</td><td>1</td>
            </tr>
        </table>
    </body>
    </html>
    """
    with patch.object(parser, 'fetch_html', return_value=mock_html):
        result = parser.parse()
        assert len(result) == 1
        assert result[0]['ticker'] == "TEST"


def test_save_to_db_source_not_found(parser):
    """Тест случая, когда в таблице source нет записи Dohod"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Имитируем, что SELECT вернул None
    mock_cursor.fetchone.return_value = None

    with patch.object(parser, '_get_db_connection', return_value=mock_conn):
        parser.save_to_db([{"ticker": "TEST"}])

        # Должен попробовать найти источник
        mock_cursor.execute.assert_called_once()
        # Но НЕ должен делать INSERT
        # (в предыдущем тесте call_count был >= 2, тут должен быть 1)
        assert mock_cursor.execute.call_count == 1


def test_save_to_db_rollback(parser):
    """Тест отката транзакции при ошибке вставки"""
    data = [{"ticker": "TEST", "company_name": "T", "sector": "S", "period": "P",
             "payment_per_share": 1, "currency": "R", "yield_percent": 1,
             "record_date_estimate": date.today(), "capitalization_mln_rub": 1, "dsi": 1}]

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.fetchone.return_value = [1]
    # При попытке INSERT вызываем ошибку
    mock_cursor.execute.side_effect = [None, Exception("DB Error")]

    with patch.object(parser, '_get_db_connection', return_value=mock_conn):
        parser.save_to_db(data)

        # Проверяем, что был вызван rollback
        mock_conn.rollback.assert_called_once()

