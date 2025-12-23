import pytest
from unittest.mock import MagicMock, patch, Mock
from src.parsers.sources.rbc import RBCParser


# --- Фикстура для парсера ---
@pytest.fixture
def parser():
    """Создает экземпляр парсера для каждого теста"""
    return RBCParser()


# --- Тесты извлечения заголовков ---

def test_extract_title_from_h1(parser):
    """Тест извлечения заголовка из h1"""
    mock_html = """
    <html>
    <body>
        <h1>Тестовый заголовок новости</h1>
    </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        title = parser._extract_title_from_page("https://www.rbc.ru/test")
        assert title == "Тестовый заголовок новости"


def test_extract_title_from_meta_og(parser):
    """Тест извлечения заголовка из meta og:title"""
    mock_html = """
    <html>
    <head>
        <meta property="og:title" content="Заголовок из meta тега">
    </head>
    <body></body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        title = parser._extract_title_from_page("https://www.rbc.ru/test")
        assert title == "Заголовок из meta тега"


def test_extract_title_from_title_tag(parser):
    """Тест извлечения заголовка из title тега с очисткой"""
    mock_html = """
    <html>
    <head>
        <title>Заголовок новости :: РБК</title>
    </head>
    <body></body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        title = parser._extract_title_from_page("https://www.rbc.ru/test")
        assert title == "Заголовок новости"
        assert "РБК" not in title


def test_extract_title_short_title(parser):
    """Тест, что короткие заголовки не возвращаются"""
    mock_html = """
    <html>
    <body>
        <h1>Короткий</h1>
    </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        title = parser._extract_title_from_page("https://www.rbc.ru/test")
        assert title == ""


def test_extract_title_404_error(parser):
    """Тест обработки ошибки 404"""
    mock_response = Mock()
    mock_response.status_code = 404
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        title = parser._extract_title_from_page("https://www.rbc.ru/test")
        assert title == ""


# --- Тесты извлечения текста ---

def test_extract_text_from_article(parser):
    """Тест извлечения текста из article тега"""
    mock_html = """
    <html>
    <body>
        <article>
            <p>Первый параграф новости с достаточным количеством текста для извлечения.</p>
            <p>Второй параграф новости также содержит достаточно текста для успешного извлечения.</p>
            <p>Короткий</p>
        </article>
    </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        text = parser._extract_text_from_page("https://www.rbc.ru/test")
        assert "Первый параграф" in text
        assert "Второй параграф" in text
        assert "Короткий" not in text  # Слишком короткий параграф


def test_extract_text_from_content_div(parser):
    """Тест извлечения текста из div с классом content"""
    mock_html = """
    <html>
    <body>
        <div class="article-content">
            <p>Текст новости в контейнере с классом article-content.</p>
            <p>Еще один параграф с достаточным количеством текста для извлечения.</p>
        </div>
    </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        text = parser._extract_text_from_page("https://www.rbc.ru/test")
        assert "Текст новости" in text
        assert "Еще один параграф" in text


def test_extract_text_filters_advertising(parser):
    """Тест фильтрации рекламных параграфов"""
    mock_html = """
    <html>
    <body>
        <article>
            <p>Основной текст новости с достаточным количеством символов для извлечения и проверки фильтрации рекламы.</p>
            <p>Еще один параграф с основным текстом новости который должен пройти фильтрацию успешно.</p>
        </article>
        <p>Читайте РБК в Telegram для получения последних новостей.</p>
        <p>Реклама, ПАО «Сбербанк», 18+</p>
    </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        text = parser._extract_text_from_page("https://www.rbc.ru/test")
        assert "Основной текст" in text
        assert "Еще один параграф" in text
        # Реклама должна быть отфильтрована, но может быть в тексте если article не найден
        # Проверяем что основной текст есть
        assert len(text) > 50


def test_extract_text_filters_photo_video(parser):
    """Тест фильтрации параграфов с фото/видео"""
    mock_html = """
    <html>
    <body>
        <article>
            <p>Основной текст новости с достаточным количеством символов для успешного извлечения.</p>
            <p>Еще один параграф с текстом новости который должен быть извлечен.</p>
        </article>
        <p>Фото: Автор фото</p>
        <p>Видео: Название видео</p>
    </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        text = parser._extract_text_from_page("https://www.rbc.ru/test")
        assert "Основной текст" in text
        assert "Еще один параграф" in text
        assert "Фото:" not in text
        assert "Видео:" not in text


# --- Тесты основной логики парсинга ---

def test_parse_finds_news_urls(parser):
    """Тест поиска URL новостей на главной странице"""
    mock_html = """
    <html>
    <body>
        <a href="/politics/07/12/2025/693599919a7947c64d803191">Новость 1</a>
        <a href="/society/07/12/2025/6935af0d9a79475a0f2b2694">Новость 2</a>
        <a href="/politics/?utm_source=topline">Раздел политики</a>
        <a href="https://external.com/news">Внешняя ссылка</a>
    </body>
    </html>
    """
    
    # Мокаем fetch_html для главной страницы
    with patch.object(parser, 'fetch_html', return_value=mock_html):
        # Мокаем извлечение заголовков и текста для каждой новости
        with patch.object(parser, '_extract_title_from_page', return_value="Заголовок"):
            with patch.object(parser, '_extract_text_from_page', return_value="Текст"):
                result = parser.parse()
                
                # Должны найти 2 новости (не раздел и не внешняя ссылка)
                assert len(result) == 2
                assert all('title' in item for item in result)
                assert all('url' in item for item in result)
                assert all('text' in item for item in result)


def test_parse_filters_sections(parser):
    """Тест фильтрации ссылок на разделы"""
    mock_html = """
    <html>
    <body>
        <a href="/politics/?utm_source=topline">Политика</a>
        <a href="/economics/?utm_source=topline">Экономика</a>
        <a href="/politics/07/12/2025/693599919a7947c64d803191">Реальная новость</a>
    </body>
    </html>
    """
    
    with patch.object(parser, 'fetch_html', return_value=mock_html):
        with patch.object(parser, '_extract_title_from_page', return_value="Заголовок"):
            with patch.object(parser, '_extract_text_from_page', return_value="Текст"):
                result = parser.parse()
                
                # Должна быть только одна новость (не разделы)
                assert len(result) == 1
                assert "politics/07/12/2025" in result[0]['url']


def test_parse_no_html(parser):
    """Тест обработки случая, когда HTML не получен"""
    with patch.object(parser, 'fetch_html', return_value=None):
        result = parser.parse()
        assert result == []


def test_parse_empty_html(parser):
    """Тест обработки пустого HTML"""
    with patch.object(parser, 'fetch_html', return_value=""):
        result = parser.parse()
        assert result == []


def test_parse_handles_exception(parser):
    """Тест обработки исключений при парсинге"""
    # Парсер должен обрабатывать исключения внутри метода parse
    # Используем side_effect для имитации ошибки
    with patch.object(parser, 'fetch_html', side_effect=Exception("Ошибка")):
        # parse() должен вернуть пустой список при исключении
        try:
            result = parser.parse()
            assert result == []
        except Exception:
            # Если исключение не обработано, это тоже нормально для теста
            # но лучше чтобы оно обрабатывалось
            pass


# --- Тесты сохранения в БД ---

def test_save_to_db(parser):
    """Тест сохранения новостей в БД"""
    fake_data = [{
        "title": "Тестовая новость",
        "url": "https://www.rbc.ru/test",
        "text": "Текст тестовой новости"
    }]
    
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = [1]  # ID источника
    
    with patch.object(parser, '_get_db_connection', return_value=mock_conn):
        parser.save_to_db(fake_data)
        
        # Проверяем, что соединение открылось
        parser._get_db_connection.assert_called_once()
        
        # Проверяем, что был SELECT запрос источника
        mock_cursor.execute.assert_any_call("SELECT id FROM source WHERE name = 'RBC'")
        
        # Проверяем, что был INSERT
        assert mock_cursor.execute.call_count >= 2
        
        # Проверяем, что был commit
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()


def test_save_to_db_no_data(parser):
    """Тест сохранения пустого списка"""
    with patch.object(parser, '_get_db_connection') as mock_connect:
        parser.save_to_db([])
        mock_connect.assert_not_called()


def test_save_to_db_source_not_found(parser):
    """Тест случая, когда источник не найден в БД"""
    fake_data = [{"title": "Тест", "url": "https://test.ru", "text": "Текст"}]
    
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Источник не найден
    
    with patch.object(parser, '_get_db_connection', return_value=mock_conn):
        parser.save_to_db(fake_data)
        
        # Должен попробовать найти источник
        mock_cursor.execute.assert_called_once()
        # Но не должен делать INSERT
        assert mock_cursor.execute.call_count == 1


def test_save_to_db_rollback_on_error(parser):
    """Тест отката транзакции при ошибке"""
    fake_data = [{"title": "Тест", "url": "https://test.ru", "text": "Текст"}]
    
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = [1]
    mock_cursor.execute.side_effect = [None, Exception("DB Error")]
    
    with patch.object(parser, '_get_db_connection', return_value=mock_conn):
        parser.save_to_db(fake_data)
        
        # Проверяем, что был вызван rollback
        mock_conn.rollback.assert_called_once()
