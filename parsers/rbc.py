"""
Парсер для сайта RBC (РБК) - новости
Сканирует главную страницу, находит URL новостей, переходит по ним и извлекает заголовки
"""
from .base_parser import BaseParser
from bs4 import BeautifulSoup
from typing import List, Dict
import re
import json
import time


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
        """
        html = self.fetch_html()
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        news_urls = []
        
        try:
            # Шаг 1: Находим все URL новостей на главной странице
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
                
                # Проверяем, что это ссылка на новость (не на раздел)
                is_news_link = any(pattern in href for pattern in news_patterns)
                is_rbc_link = 'rbc.ru' in href or href.startswith('/')
                
                # Исключаем ссылки на разделы (они обычно короткие или без ID)
                # Ссылки на статьи обычно содержат длинный ID (например, /politics/07/12/2025/693599919a7947c64d803191)
                is_section = any(exclude in href for exclude in ['/politics/?', '/economics/?', '/business/?', 
                                                                  '/society/?', '/technology/?', '/finance/?',
                                                                  '?utm_source=', 'story/68822f889a79475439ba67bb'])  # Исключаем служебные story
                
                # Проверяем, что это ссылка на конкретную статью (содержит дату или длинный ID)
                has_article_id = bool(re.search(r'/\d{2}/\d{2}/\d{4}/[a-f0-9]+', href)) or bool(re.search(r'/[a-f0-9]{24}', href))
                
                if is_news_link and is_rbc_link and not is_section and (has_article_id or len(text) > 15):
                    # Формируем полный URL
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = f"https://www.rbc.ru{href}"
                    
                    # Убираем параметры для дедупликации
                    clean_url = full_url.split('?')[0]
                    
                    if clean_url not in seen_urls:
                        seen_urls.add(clean_url)
                        news_urls.append(full_url)
            
            # Шаг 2: Переходим по каждому URL и извлекаем заголовки
            news_items = []
            for url in news_urls[:30]:  # Ограничиваем до 30 новостей для скорости
                try:
                    title = self._extract_title_from_page(url)
                    if title:
                        news_items.append({
                            "title": title,
                            "url": url
                        })
                    # Небольшая задержка, чтобы не перегружать сервер
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Ошибка при парсинге {url}: {e}")
                    continue
            
            return news_items
            
        except Exception as e:
            print(f"Ошибка при парсинге: {e}")
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
            
            # Способ 1: Ищем в h1
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
                if title and len(title) > 10:
                    return title
            
            # Способ 2: Ищем в meta og:title
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                title = meta_title.get('content', '').strip()
                if title and len(title) > 10:
                    return title
            
            # Способ 3: Ищем в title теге
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
                # Убираем " :: РБК" и подобное
                title = re.sub(r'\s*::\s*РБК.*$', '', title)
                if title and len(title) > 10:
                    return title
            
            # Способ 4: Ищем в элементах с классом title
            title_elem = soup.find(['h1', 'h2'], class_=lambda x: x and 'title' in str(x).lower())
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 10:
                    return title
            
            return ""
            
        except Exception as e:
            print(f"Ошибка при извлечении заголовка из {url}: {e}")
            return ""


if __name__ == "__main__":
    parser = RBCParser()
    data = parser.get_parsed_data()
    print(data)
