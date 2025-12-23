import pytest
from unittest.mock import MagicMock, patch, Mock
from src.parsers.sources.base_parser import BaseParser


# --- Тесты инициализации ---

def test_init_with_default_headers():
    """Тест инициализации с дефолтными заголовками"""
    parser = BaseParser("https://example.com")
    assert parser.url == "https://example.com"
    assert parser.headers is not None
    assert 'User-Agent' in parser.headers
    assert parser.session is not None


def test_init_with_custom_headers():
    """Тест инициализации с кастомными заголовками"""
    custom_headers = {'User-Agent': 'Custom Agent', 'Accept': 'text/html'}
    parser = BaseParser("https://example.com", headers=custom_headers)
    assert parser.headers == custom_headers
    assert parser.session.headers['User-Agent'] == 'Custom Agent'


# --- Тесты fetch_html ---

def test_fetch_html_success():
    """Тест успешного получения HTML"""
    parser = BaseParser("https://example.com")
    mock_response = Mock()
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.raise_for_status = Mock()
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        html = parser.fetch_html()
        assert html == "<html><body>Test</body></html>"
        mock_response.raise_for_status.assert_called_once()


def test_fetch_html_request_exception():
    """Тест обработки исключения при запросе"""
    import requests
    parser = BaseParser("https://example.com")
    
    with patch.object(parser.session, 'get', side_effect=requests.RequestException("Connection error")):
        html = parser.fetch_html()
        assert html is None


def test_fetch_html_http_error():
    """Тест обработки HTTP ошибки"""
    import requests
    parser = BaseParser("https://example.com")
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        html = parser.fetch_html()
        assert html is None


# --- Тесты to_json ---

def test_to_json():
    """Тест преобразования данных в JSON"""
    parser = BaseParser("https://example.com")
    data = [
        {"name": "Test", "value": 123},
        {"name": "Test2", "value": 456}
    ]
    
    json_str = parser.to_json(data)
    assert isinstance(json_str, str)
    assert "Test" in json_str
    assert "123" in json_str
    # Проверяем, что это валидный JSON
    import json
    parsed = json.loads(json_str)
    assert len(parsed) == 2


def test_to_json_empty_list():
    """Тест преобразования пустого списка"""
    parser = BaseParser("https://example.com")
    json_str = parser.to_json([])
    assert json_str == "[]"


def test_to_json_unicode():
    """Тест преобразования данных с кириллицей"""
    parser = BaseParser("https://example.com")
    data = [{"name": "Тест", "value": "Значение"}]
    
    json_str = parser.to_json(data)
    assert "Тест" in json_str
    assert "Значение" in json_str


# --- Тесты NotImplementedError ---

def test_parse_not_implemented():
    """Тест, что parse() выбрасывает NotImplementedError"""
    parser = BaseParser("https://example.com")
    with pytest.raises(NotImplementedError):
        parser.parse()


def test_save_to_db_not_implemented():
    """Тест, что save_to_db() выбрасывает NotImplementedError"""
    parser = BaseParser("https://example.com")
    with pytest.raises(NotImplementedError):
        parser.save_to_db([{"test": "data"}])


# --- Тесты get_parsed_data ---

def test_get_parsed_data():
    """Тест получения данных в формате JSON"""
    parser = BaseParser("https://example.com")
    
    # Мокаем parse() чтобы вернуть тестовые данные
    test_data = [{"name": "Test", "value": 123}]
    with patch.object(parser, 'parse', return_value=test_data):
        result = parser.get_parsed_data()
        assert isinstance(result, str)
        assert "Test" in result
        assert "123" in result


def test_get_parsed_data_empty():
    """Тест получения пустых данных"""
    parser = BaseParser("https://example.com")
    
    with patch.object(parser, 'parse', return_value=[]):
        result = parser.get_parsed_data()
        assert result == "[]"


# --- Тесты _get_db_connection ---

def test_get_db_session():
    """Тест создания сессии БД через SQLAlchemy"""
    parser = BaseParser("https://example.com")
    
    mock_session = MagicMock()
    with patch('src.parsers.sources.base_parser.get_sync_session', return_value=mock_session):
        session = parser._get_db_session()
        assert session == mock_session


def test_get_source_by_name():
    """Тест получения источника по имени"""
    parser = BaseParser("https://example.com")
    
    mock_session = MagicMock()
    mock_source = MagicMock()
    mock_source.name = "RBC"
    mock_source.id = 1
    
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_source
    mock_session.query.return_value = mock_query
    
    with patch.object(parser, '_get_db_session', return_value=mock_session):
        source = parser._get_source_by_name(mock_session, "RBC")
        assert source == mock_source
        mock_session.query.assert_called_once()

