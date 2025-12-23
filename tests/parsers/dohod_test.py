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
    """Проверяем, что метод использует SQLAlchemy для сохранения в БД"""

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

    # Создаем моки для сессии SQLAlchemy
    mock_session = MagicMock()
    mock_source = MagicMock()
    mock_source.id = 1
    
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_source
    mock_session.query.return_value = mock_query

    # Подменяем _get_db_session в парсере
    with patch.object(parser, '_get_db_session', return_value=mock_session):
        parser.save_to_db(fake_data)

        # Проверяем, что сессия была получена
        parser._get_db_session.assert_called_once()

        # Проверяем, что был запрос источника
        mock_session.query.assert_called()

        # Проверяем, что был add для добавления записи
        assert mock_session.add.called

        # Проверяем, что был commit
        mock_session.commit.assert_called_once()
        # Проверяем, что закрыли соединение
        mock_session.close.assert_called_once()


def test_save_to_db_no_data(parser):
    """Проверка выхода, если данных нет"""
    with patch.object(parser, '_get_db_session') as mock_session:
        parser.save_to_db([])
        mock_session.assert_not_called()


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
    mock_session = MagicMock()
    mock_query = MagicMock()
    # Имитируем, что источник не найден
    mock_query.filter.return_value.first.return_value = None
    mock_session.query.return_value = mock_query

    with patch.object(parser, '_get_db_session', return_value=mock_session):
        parser.save_to_db([{"ticker": "TEST", "company_name": "T", "sector": "S", "period": "P",
                           "payment_per_share": 1, "currency": "R", "yield_percent": 1,
                           "record_date_estimate": date.today(), "capitalization_mln_rub": 1, "dsi": 1}])

        # Должен попробовать найти источник
        mock_session.query.assert_called()
        # Но НЕ должен делать add
        mock_session.add.assert_not_called()


def test_save_to_db_rollback(parser):
    """Тест отката транзакции при ошибке вставки"""
    data = [{"ticker": "TEST", "company_name": "T", "sector": "S", "period": "P",
             "payment_per_share": 1, "currency": "R", "yield_percent": 1,
             "record_date_estimate": date.today(), "capitalization_mln_rub": 1, "dsi": 1}]

    mock_session = MagicMock()
    mock_source = MagicMock()
    mock_source.id = 1
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_source
    mock_session.query.return_value = mock_query
    # При попытке add вызываем ошибку
    mock_session.add.side_effect = Exception("DB Error")

    with patch.object(parser, '_get_db_session', return_value=mock_session):
        parser.save_to_db(data)

        # Проверяем, что был вызван rollback
        mock_session.rollback.assert_called_once()


# --- Дополнительные тесты для увеличения покрытия ---


def test_run_dohod_parser_success():
    """Тест успешного сценария run_dohod_parser"""
    from src.parsers.sources import dohod
    
    with patch.object(dohod, "logging") as mock_logging, patch.object(
        dohod, "DohodParser"
    ) as mock_cls:
        parser_instance = MagicMock()
        parser_instance.parse.return_value = [{"ticker": "OK"}]
        parser_instance.save_to_db.return_value = None
        mock_cls.return_value = parser_instance
        
        dohod.run_dohod_parser()
        
        mock_logging.basicConfig.assert_called_once()
        mock_cls.assert_called_once()
        parser_instance.parse.assert_called_once()
        parser_instance.save_to_db.assert_called_once()


def test_run_dohod_parser_empty_data():
    """Тест run_dohod_parser с пустым списком данных"""
    from src.parsers.sources import dohod
    
    with patch.object(dohod, "logging") as mock_logging, patch.object(
        dohod, "DohodParser"
    ) as mock_cls:
        parser_instance = MagicMock()
        parser_instance.parse.return_value = []
        mock_cls.return_value = parser_instance
        
        with patch.object(dohod.logger, "warning") as mock_warning:
            dohod.run_dohod_parser()
            mock_warning.assert_called()


def test_run_dohod_parser_handles_exception():
    """Тест обработки исключения внутри run_dohod_parser"""
    from src.parsers.sources import dohod
    
    with patch.object(dohod, "logging") as mock_logging, patch.object(
        dohod, "DohodParser"
    ) as mock_cls:
        parser_instance = MagicMock()
        parser_instance.parse.side_effect = RuntimeError("boom")
        mock_cls.return_value = parser_instance
        
        with patch.object(dohod.logger, "error") as mock_error:
            dohod.run_dohod_parser()
            mock_error.assert_called()


def test_save_to_db_multiple_items(parser):
    """Тест сохранения нескольких записей"""
    fake_data = [
        {"ticker": "TEST1", "company_name": "T1", "sector": "S", "period": "P",
         "payment_per_share": 1, "currency": "R", "yield_percent": 1,
         "record_date_estimate": date.today(), "capitalization_mln_rub": 1, "dsi": 1},
        {"ticker": "TEST2", "company_name": "T2", "sector": "S", "period": "P",
         "payment_per_share": 2, "currency": "R", "yield_percent": 2,
         "record_date_estimate": date.today(), "capitalization_mln_rub": 2, "dsi": 2},
    ]
    
    mock_session = MagicMock()
    mock_source = MagicMock()
    mock_source.id = 1
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_source
    mock_session.query.return_value = mock_query
    
    with patch.object(parser, '_get_db_session', return_value=mock_session):
        parser.save_to_db(fake_data)
        
        # Должно быть вызвано add дважды (для двух записей)
        assert mock_session.add.call_count == 2
        mock_session.commit.assert_called_once()


def test_save_to_db_connection_error(parser):
    """Тест обработки ошибки подключения к БД"""
    fake_data = [{"ticker": "TEST", "company_name": "T", "sector": "S", "period": "P",
                  "payment_per_share": 1, "currency": "R", "yield_percent": 1,
                  "record_date_estimate": date.today(), "capitalization_mln_rub": 1, "dsi": 1}]
    
    with patch.object(parser, '_get_db_session', side_effect=Exception("Connection error")):
        # Не должно быть исключения, только логирование
        parser.save_to_db(fake_data)


def test_save_to_db_close_error(parser):
    """Тест обработки ошибки при закрытии соединения"""
    fake_data = [{"ticker": "TEST", "company_name": "T", "sector": "S", "period": "P",
                  "payment_per_share": 1, "currency": "R", "yield_percent": 1,
                  "record_date_estimate": date.today(), "capitalization_mln_rub": 1, "dsi": 1}]
    
    mock_session = MagicMock()
    mock_source = MagicMock()
    mock_source.id = 1
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_source
    mock_session.query.return_value = mock_query
    mock_session.close.side_effect = Exception("Close error")
    
    with patch.object(parser, '_get_db_session', return_value=mock_session):
        try:
            parser.save_to_db(fake_data)
        except Exception:
            pass  # Ожидаемое исключение при close
        
        mock_session.commit.assert_called_once()

