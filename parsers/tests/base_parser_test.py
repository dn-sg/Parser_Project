import pytest
from unittest.mock import MagicMock, patch, Mock
from parsers.base_parser import BaseParser


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

def test_get_db_connection():
    """Тест создания подключения к БД"""
    parser = BaseParser("https://example.com")
    
    mock_conn = MagicMock()
    with patch('parsers.base_parser.pg8000.dbapi.connect', return_value=mock_conn):
        with patch.dict('os.environ', {
            'POSTGRES_HOST': 'test_host',
            'POSTGRES_PORT': '5433',
            'POSTGRES_DB': 'test_db',
            'POSTGRES_USER': 'test_user',
            'POSTGRES_PASSWORD': 'test_pass'
        }):
            conn = parser._get_db_connection()
            assert conn == mock_conn


def test_get_db_connection_defaults():
    """Тест создания подключения с дефолтными значениями"""
    parser = BaseParser("https://example.com")
    
    mock_conn = MagicMock()
    with patch('parsers.base_parser.pg8000.dbapi.connect', return_value=mock_conn) as mock_connect:
        # Удаляем переменные окружения для host и port, чтобы проверить дефолты
        import os
        original_host = os.environ.pop('POSTGRES_HOST', None)
        original_port = os.environ.pop('POSTGRES_PORT', None)
        
        try:
            with patch.dict('os.environ', {
                'POSTGRES_DB': 'test_db',
                'POSTGRES_USER': 'test_user',
                'POSTGRES_PASSWORD': 'test_pass'
            }, clear=False):
                conn = parser._get_db_connection()
                # Проверяем, что использовались дефолтные значения для host и port
                mock_connect.assert_called_once()
                call_args = mock_connect.call_args[1]
                assert call_args['host'] == 'localhost'  # дефолт
                assert call_args['port'] == '5432'  # дефолт
        finally:
            # Восстанавливаем оригинальные значения
            if original_host:
                os.environ['POSTGRES_HOST'] = original_host
            if original_port:
                os.environ['POSTGRES_PORT'] = original_port

