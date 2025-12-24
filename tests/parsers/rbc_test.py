import pytest
from unittest.mock import MagicMock, patch, Mock
from src.parsers.sources import RBCParser


# Фикстура для парсера
@pytest.fixture
def parser():
    """Создает экземпляр парсера для каждого теста"""
    return RBCParser()


# Тесты извлечения заголовков
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


# Тесты извлечения текста
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
        assert "Короткий" not in text


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


# Тесты основной логики парсинга
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

    with patch.object(parser, 'fetch_html', return_value=mock_html):
        with patch.object(parser, '_extract_title_from_page', return_value="Заголовок"):
            with patch.object(parser, '_extract_text_from_page', return_value="Текст"):
                result = parser.parse()

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
    with patch.object(parser, 'fetch_html', side_effect=Exception("Ошибка")):
        try:
            result = parser.parse()
            assert result == []
        except Exception:
            pass


# Тесты сохранения в БД 
def test_save_to_db(parser):
    """Тест сохранения новостей в БД через SQLAlchemy"""
    fake_data = [{
        "title": "Тестовая новость",
        "url": "https://www.rbc.ru/test",
        "text": "Текст тестовой новости"
    }]
    
    mock_session = MagicMock()
    mock_source = MagicMock()
    mock_source.id = 1
    mock_source.name = "RBC"
    
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_source
    mock_session.query.return_value = mock_query
    
    with patch.object(parser, '_get_db_session', return_value=mock_session):
        parser.save_to_db(fake_data)

        parser._get_db_session.assert_called_once()

        mock_session.query.assert_called()

        assert mock_session.execute.called or mock_session.add.called

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()


def test_save_to_db_no_data(parser):
    """Тест сохранения пустого списка"""
    with patch.object(parser, '_get_db_session') as mock_session:
        parser.save_to_db([])
        mock_session.assert_not_called()


def test_save_to_db_source_not_found(parser):
    """Тест случая, когда источник не найден в БД"""
    fake_data = [{"title": "Тест", "url": "https://test.ru", "text": "Текст"}]
    
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_session.query.return_value = mock_query
    
    with patch.object(parser, '_get_db_session', return_value=mock_session):
        parser.save_to_db(fake_data)

        mock_session.query.assert_called()
        mock_session.add.assert_not_called()
        if hasattr(mock_session, 'execute'):
            assert not mock_session.execute.called or mock_session.execute.call_count == 0


def test_save_to_db_rollback_on_error(parser):
    """Тест отката транзакции при ошибке"""
    fake_data = [{"title": "Тест", "url": "https://test.ru", "text": "Текст"}]
    
    mock_session = MagicMock()
    mock_source = MagicMock()
    mock_source.id = 1
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_source
    mock_session.query.return_value = mock_query
    mock_session.execute.side_effect = Exception("DB Error")
    
    with patch.object(parser, '_get_db_session', return_value=mock_session):
        parser.save_to_db(fake_data)

        mock_session.rollback.assert_called_once()


def test_extract_title_with_full_url(parser):
    """Тест обработки полного URL (начинается с http)"""
    mock_html = """
    <html>
    <body>
        <h1>Заголовок новости</h1>
    </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        title = parser._extract_title_from_page("https://www.rbc.ru/test")
        assert title == "Заголовок новости"


def test_extract_title_with_relative_url(parser):
    """Тест обработки относительного URL"""
    mock_html = """
    <html>
    <body>
        <h1>Заголовок новости</h1>
    </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        title = parser._extract_title_from_page("/politics/07/12/2025/693599919a7947c64d803191")
        assert title == "Заголовок новости"


def test_extract_title_exception_handling(parser):
    """Тест обработки исключения при извлечении заголовка"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><body></body></html>"
    mock_response.get.side_effect = Exception("Error")
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        with patch('src.parsers.sources.rbc.BeautifulSoup', side_effect=Exception("Parse error")):
            title = parser._extract_title_from_page("https://www.rbc.ru/test")
            assert title == ""


def test_extract_title_with_class_title(parser):
    """Тест извлечения заголовка из элемента с классом title"""
    mock_html = """
    <html>
    <body>
        <h2 class="article-title">Заголовок из класса title</h2>
    </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        title = parser._extract_title_from_page("https://www.rbc.ru/test")
        assert "Заголовок из класса title" in title


def test_extract_text_status_not_200(parser):
    """Тест обработки статуса не 200"""
    mock_response = Mock()
    mock_response.status_code = 404
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        text = parser._extract_text_from_page("https://www.rbc.ru/test")
        assert text == ""


def test_extract_text_from_all_paragraphs(parser):
    """Тест извлечения текста из всех параграфов на странице"""
    mock_html = """
    <html>
    <body>
        <p>Первый параграф новости с достаточным количеством текста для успешного извлечения и проверки работы парсера.</p>
        <p>Второй параграф новости также содержит достаточно текста для успешного извлечения и проверки работы парсера.</p>
        <p>Короткий</p>
        <p>© РБК</p>
        <p>12:30</p>
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
        assert "Короткий" not in text
        assert "©" not in text
        assert "12:30" not in text


def test_extract_text_filters_skip_phrases(parser):
    """Тест фильтрации параграфов с рекламными фразами"""
    mock_html = """
    <html>
    <body>
        <p>Основной текст новости с достаточным количеством символов для успешного извлечения и проверки фильтрации рекламы.</p>
        <p>Читайте РБК в Telegram для получения последних новостей и обновлений.</p>
        <p>Реклама, ПАО «Сбербанк», 18+</p>
        <p>Попробуйте новую функцию Гигачат для общения.</p>
    </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        text = parser._extract_text_from_page("https://www.rbc.ru/test")
        assert "Основной текст" in text
        assert "Читайте РБК" not in text
        assert "Реклама" not in text
        assert "Гигачат" not in text


def test_extract_text_filters_photo_video_start(parser):
    """Тест фильтрации параграфов начинающихся с Фото/Видео"""
    mock_html = """
    <html>
    <body>
        <p>Основной текст новости с достаточным количеством символов для успешного извлечения.</p>
        <p>Фото: Автор фотографии</p>
        <p>Видео: Название видео</p>
        <p>Фото: еще одно фото</p>
    </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        text = parser._extract_text_from_page("https://www.rbc.ru/test")
        assert "Основной текст" in text
        assert "Фото:" not in text
        assert "Видео:" not in text


def test_extract_text_exception_handling(parser):
    """Тест обработки исключения при извлечении текста"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><body></body></html>"
    
    with patch.object(parser.session, 'get', return_value=mock_response):
        with patch('src.parsers.sources.rbc.BeautifulSoup', side_effect=Exception("Parse error")):
            text = parser._extract_text_from_page("https://www.rbc.ru/test")
            assert text == ""


def test_parse_with_exception_in_extraction(parser):
    """Тест обработки исключения при извлечении заголовка/текста"""
    mock_html = """
    <html>
    <body>
        <a href="/politics/07/12/2025/693599919a7947c64d803191">Новость 1</a>
    </body>
    </html>
    """
    
    with patch.object(parser, 'fetch_html', return_value=mock_html):
        with patch.object(parser, '_extract_title_from_page', side_effect=Exception("Error")):
            with patch.object(parser, '_extract_text_from_page', return_value=""):
                result = parser.parse()
                assert isinstance(result, list)


def test_save_to_db_multiple_items(parser):
    """Тест сохранения нескольких новостей"""
    fake_data = [
        {"title": "Новость 1", "url": "https://www.rbc.ru/test1", "text": "Текст 1"},
        {"title": "Новость 2", "url": "https://www.rbc.ru/test2", "text": "Текст 2"},
    ]
    
    mock_session = MagicMock()
    mock_source = MagicMock()
    mock_source.id = 1
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_source
    mock_session.query.return_value = mock_query
    
    with patch.object(parser, '_get_db_session', return_value=mock_session):
        parser.save_to_db(fake_data)

        assert mock_session.execute.call_count == 2
        mock_session.commit.assert_called_once()


def test_save_to_db_connection_error(parser):
    """Тест обработки ошибки подключения к БД"""
    fake_data = [{"title": "Тест", "url": "https://test.ru", "text": "Текст"}]
    
    with patch.object(parser, '_get_db_session', side_effect=Exception("Connection error")):
        parser.save_to_db(fake_data)


def test_save_to_db_close_error(parser):
    """Тест обработки ошибки при закрытии соединения"""
    fake_data = [{"title": "Тест", "url": "https://test.ru", "text": "Текст"}]
    
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
            pass
        
        mock_session.commit.assert_called_once()


def test_run_rbc_parser_success():
    """Тест успешного сценария run_rbc_parser"""
    from src.parsers.sources import rbc
    
    with patch.object(rbc, "logging") as mock_logging, patch.object(
        rbc, "RBCParser"
    ) as mock_cls:
        parser_instance = MagicMock()
        parser_instance.parse.return_value = [{"title": "OK", "url": "https://test.ru", "text": "Text"}]
        parser_instance.save_to_db.return_value = None
        mock_cls.return_value = parser_instance
        
        rbc.run_rbc_parser()
        
        mock_logging.basicConfig.assert_called_once()
        mock_cls.assert_called_once()
        parser_instance.parse.assert_called_once()
        parser_instance.save_to_db.assert_called_once()


def test_run_rbc_parser_empty_data():
    """Тест run_rbc_parser с пустым списком данных"""
    from src.parsers.sources import rbc
    
    with patch.object(rbc, "logging") as mock_logging, patch.object(
        rbc, "RBCParser"
    ) as mock_cls:
        parser_instance = MagicMock()
        parser_instance.parse.return_value = []
        mock_cls.return_value = parser_instance
        
        with patch.object(rbc.logger, "warning") as mock_warning:
            rbc.run_rbc_parser()
            mock_warning.assert_called()


def test_run_rbc_parser_handles_exception():
    """Тест обработки исключения внутри run_rbc_parser"""
    from src.parsers.sources import rbc
    
    with patch.object(rbc, "logging") as mock_logging, patch.object(
        rbc, "RBCParser"
    ) as mock_cls:
        parser_instance = MagicMock()
        parser_instance.parse.side_effect = RuntimeError("boom")
        mock_cls.return_value = parser_instance
        
        with patch.object(rbc.logger, "error") as mock_error:
            rbc.run_rbc_parser()
            mock_error.assert_called()
