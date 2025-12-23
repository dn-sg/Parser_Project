"""
Парсер для сайта RBC (РБК) - новости
Сканирует главную страницу, находит URL новостей, переходит по ним и извлекает заголовки
"""
from .base_parser import BaseParser
from bs4 import BeautifulSoup
from typing import List, Dict
import re
import time
import logging

logger = logging.getLogger(__name__)
class RBCParser(BaseParser):
    """Парсер для сайта РБК - главная страница с новостями"""
    
    def __init__(self):
        """Инициализация парсера для главной страницы РБК"""
        super().__init__("https://www.rbc.ru/")
    
    def parse(self) -> List[Dict]:
        """
        Парсинг новостей с сайта РБК
        1. Сканирует главную страницу
        2. Находит URL новостей
        3. Переходит по каждому URL
        4. Извлекает заголовки со страниц новостей
        
        Returns:
            Список словарей с данными о новостях:
            - title: заголовок новости (полный, со страницы статьи)
            - url: ссылка на новость
            - text: текст новости
        """
        html = self.fetch_html()
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        news_urls = []
        
        try:
            # Нахожу все URL новостей на главной странице
            all_links = soup.find_all('a', href=True)
            
            # Паттерны для новостей
            news_patterns = [
                '/article/', '/news/', '/story/',
                '/politics/', '/economics/', '/business/',
                '/society/', '/technology/', '/finance/',
                '/rbcfreenews/', '/life/', '/style/',
                '/books/', '/person/', '/designs/',
                'pro.rbc.ru/demo/', 'pro.rbc.ru/books/',
                'style.rbc.ru/'
            ]
            
            seen_urls = set()
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                is_news_link = any(pattern in href for pattern in news_patterns)
                is_rbc_link = 'rbc.ru' in href or href.startswith('/')
                
                is_section = any(exclude in href for exclude in ['/politics/?', '/economics/?', '/business/?', 
                                                                  '/society/?', '/technology/?', '/finance/?',
                                                                  '?utm_source=', 'story/68822f889a79475439ba67bb'])
                
                # Проверяю, что это ссылка на конкретную статью
                has_article_id = bool(re.search(r'/\d{2}/\d{2}/\d{4}/[a-f0-9]+', href)) or bool(re.search(r'/[a-f0-9]{24}', href))
                
                if is_news_link and is_rbc_link and not is_section and (has_article_id or len(text) > 15):
                    # Формирую полный URL
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = f"https://www.rbc.ru{href}"
                    
                    # Убираю параметры для дедупликации
                    clean_url = full_url.split('?')[0]
                    
                    if clean_url not in seen_urls:
                        seen_urls.add(clean_url)
                        news_urls.append(full_url)
            
            # Перехожу по каждому URL и извлекаю заголовки и текст
            news_items = []
            for url in news_urls[:30]:
                try:
                    title = self._extract_title_from_page(url)
                    text = self._extract_text_from_page(url)
                    if title:
                        news_items.append({
                            "title": title,
                            "url": url,
                            "text": text
                        })
                    time.sleep(0.1)
                except Exception as e:
                    logger.warning(f"Ошибка при парсинге {url}: {e}")
                    continue
            
            return news_items
            
        except Exception as e:
            logger.error(f"Критическая ошибка при парсинге: {e}", exc_info=True)
            return []
    
    def _extract_title_from_page(self, url: str) -> str:
        """
        Извлекает заголовок со страницы новости
        
        Args:
            url: URL страницы новости
            
        Returns:
            Заголовок новости или пустая строка
        """
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищу в h1
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
                if title and len(title) > 10:
                    return title
            
            # Ищу в meta og:title
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                title = meta_title.get('content', '').strip()
                if title and len(title) > 10:
                    return title
            
            # Ищу в title теге
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
                title = re.sub(r'\s*::\s*РБК.*$', '', title)
                if title and len(title) > 10:
                    return title
            
            # Ищу в элементах с классом title
            title_elem = soup.find(['h1', 'h2'], class_=lambda x: x and 'title' in str(x).lower())
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 10:
                    return title
            
            return ""
            
        except Exception as e:
            logger.warning(f"Ошибка заголовка {url}: {e}")
            return ""
    
    def _extract_text_from_page(self, url: str) -> str:
        """
        Извлекает текст новости со страницы статьи
        
        Args:
            url: URL страницы новости
            
        Returns:
            Текст новости или пустая строка
        """
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищу article тег
            article = soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                if paragraphs:
                    text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                    text_parts = [p for p in text_parts if len(p) > 20]
                    if text_parts:
                        return ' '.join(text_parts)
            
            # Ищу div
            content_divs = soup.find_all(['div', 'section'], class_=lambda x: x and any(
                word in str(x).lower() for word in ['article', 'text', 'content', 'body', 'story']
            ))
            
            for div in content_divs:
                paragraphs = div.find_all('p')
                if paragraphs:
                    text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                    text_parts = [p for p in text_parts if len(p) > 20]
                    if text_parts:
                        return ' '.join(text_parts)
            
            # Ищу все параграфы на странице
            all_paragraphs = soup.find_all('p')
            if all_paragraphs:
                text_parts = []
                skip_words = ['подписка', 'реклама', 'cookie', 'политика конфиденциальности', 
                             'читайте также', 'подробнее', 'источник', 'фото:', 'фото']
                for p in all_paragraphs:
                    text = p.get_text(strip=True)
                    if (len(text) > 50 and 
                        not any(skip in text.lower() for skip in skip_words) and
                        not text.startswith('©') and
                        not re.match(r'^\d{1,2}:\d{2}', text)):
                        text_parts.append(text)
                
                if text_parts:
                    # Фильтрую параграфы
                    filtered_parts = []
                    skip_phrases = [
                        'читайте рбк', 'реклама', 'подписка', 'cookie', 
                        'политика конфиденциальности', 'какое вино подать',
                        'как приготовить', 'чем занять детей', 'как легко завести разговор',
                        'из каких сыров', 'что делать, если пролил', 'какие есть правила',
                        'какие игры можно', 'как легко запомнить', 'попробуйте новую функцию',
                        'гигачат', 'пао «сбербанк»', '18+'
                    ]
                    
                    for p in text_parts:
                        if len(p) < 50:
                            continue
                        if any(phrase in p.lower() for phrase in skip_phrases):
                            continue
                        if re.match(r'^(Фото|Видео|Фото:|Видео:)', p, re.I):
                            continue
                        filtered_parts.append(p)
                    
                    if filtered_parts:
                        main_text = [p for p in filtered_parts if len(p) > 100]
                        if main_text:
                            return ' '.join(main_text[:15])
                        else:
                            return ' '.join(filtered_parts[:10])
            
            return ""
            
        except Exception as e:
            logger.warning(f"Ошибка текста {url}: {e}")
            return ""

    # Сохраняю в БД
    def save_to_db(self, data: List[Dict]) -> None:
        """Сохранение новостей в таблицу rbc_news через SQLAlchemy"""
        if not data:
            logger.warning("Нет данных для сохранения в БД.")
            return

        session = None
        try:
            session = self._get_db_session()
            # Получаю источник
            source = self._get_source_by_name(session, "RBC")
            if not source:
                logger.error("Ошибка: Источник 'RBC' не найден в таблице source.")
                return

            # Импортирую модель
            from src.database import RBCNews
            from sqlalchemy.dialects.postgresql import insert

            # Вставляю данные с обработкой конфликтов
            for item in data:
                stmt = insert(RBCNews).values(
                    source_id=source.id,
                    title=item.get("title"),
                    url=item.get("url"),
                    text=item.get("text")
                )
                stmt = stmt.on_conflict_do_nothing(index_elements=['url'])
                
                session.execute(stmt)

            session.commit()
            logger.info(f"Успешно обработано {len(data)} новостей для БД.")

        except Exception as e:
            logger.error(f"Ошибка при сохранении в БД: {e}", exc_info=True)
            if session:
                session.rollback()
        finally:
            if session:
                session.close()


def run_rbc_parser():
    """Функция запуска парсера RBC"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        parser = RBCParser()
        logger.info("Начинаем парсинг RBC...")

        # Парсинг
        news_list = parser.parse()

        if news_list:
            logger.info(f"Спарсено {len(news_list)} новостей.")

            # Сохранение в БД
            logger.info("Сохраняем в БД...")
            parser.save_to_db(news_list)

            logger.info("Все операции завершены успешно.")
        else:
            logger.warning("Список новостей пуст.")

    except Exception as e:
        logger.error(f"Ошибка запуска RBC: {e}", exc_info=True)


if __name__ == "__main__":
    run_rbc_parser()