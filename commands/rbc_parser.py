"""
Парсер для сайта RBC (РБК) - новости
Применяет SOLID принципы и устраняет дублирование кода
"""
from bs4 import BeautifulSoup
from typing import List, Dict
import re
import time
import logging
from .base_parser import BaseParser
from .html_extractor import HTMLExtractor
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from adapters.http_client import IHttpClient

logger = logging.getLogger(__name__)


class RBCParser(BaseParser):
    """Парсер для сайта РБК - главная страница с новостями"""
    
    def __init__(self, http_client: IHttpClient = None):
        """Инициализация парсера для главной страницы РБК"""
        super().__init__("https://www.rbc.ru/", http_client)
        self.extractor = HTMLExtractor()
    
    def parse(self) -> List[Dict]:
        """
        Парсинг новостей с сайта РБК
        1. Сканирует главную страницу
        2. Находит URL новостей
        3. Переходит по каждому URL
        4. Извлекает заголовки со страниц новостей
        
        Returns:
            Список словарей с данными о новостях
        """
        html = self.fetch_html()
        soup = BeautifulSoup(html, 'html.parser')
        news_urls = self._extract_news_urls(soup)
        
        # Извлекаем данные со страниц новостей
        news_items = []
        for url in news_urls[:30]:  # Ограничиваем до 30 новостей
            try:
                title, text = self._extract_news_data(url)
                if title:
                    news_items.append({
                        "title": title,
                        "url": url,
                        "text": text
                    })
                time.sleep(0.1)  # Задержка, чтобы не перегружать сервер
            except Exception as e:
                logger.warning(f"Ошибка при парсинге {url}: {e}")
                continue
        
        return news_items
    
    def _extract_news_urls(self, soup: BeautifulSoup) -> List[str]:
        """Извлечение URL новостей с главной страницы"""
        all_links = soup.find_all('a', href=True)
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
        news_urls = []
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            is_news_link = any(pattern in href for pattern in news_patterns)
            is_rbc_link = 'rbc.ru' in href or href.startswith('/')
            is_section = any(exclude in href for exclude in [
                '/politics/?', '/economics/?', '/business/?',
                '/society/?', '/technology/?', '/finance/?',
                '?utm_source=', 'story/68822f889a79475439ba67bb'
            ])
            has_article_id = bool(re.search(r'/\d{2}/\d{2}/\d{4}/[a-f0-9]+', href)) or bool(
                re.search(r'/[a-f0-9]{24}', href))
            
            if is_news_link and is_rbc_link and not is_section and (has_article_id or len(text) > 15):
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = f"https://www.rbc.ru{href}"
                
                clean_url = full_url.split('?')[0]
                if clean_url not in seen_urls:
                    seen_urls.add(clean_url)
                    news_urls.append(full_url)
        
        return news_urls
    
    def _extract_news_data(self, url: str):
        """
        Извлечение заголовка и текста со страницы новости
        
        Args:
            url: URL страницы новости
            
        Returns:
            Кортеж (заголовок, текст)
        """
        html = self.http_client.get_html(url)
        if not html:
            return "", ""
        
        soup = BeautifulSoup(html, 'html.parser')
        title = self.extractor.extract_title(soup)
        text = self.extractor.extract_text(soup)
        
        return title, text

