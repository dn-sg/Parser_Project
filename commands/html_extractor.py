"""
Утилиты для извлечения данных из HTML (DRY - общая логика)
"""
from bs4 import BeautifulSoup
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)


class HTMLExtractor:
    """Класс для извлечения данных из HTML (устраняет дублирование)"""
    
    @staticmethod
    def extract_title(soup: BeautifulSoup) -> str:
        """
        Извлечение заголовка из HTML (общая логика для всех парсеров)
        
        Args:
            soup: BeautifulSoup объект
            
        Returns:
            Заголовок или пустая строка
        """
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
    
    @staticmethod
    def extract_text(soup: BeautifulSoup) -> str:
        """
        Извлечение текста статьи из HTML (общая логика)
        
        Args:
            soup: BeautifulSoup объект
            
        Returns:
            Текст статьи или пустая строка
        """
        # Способ 1: Ищем article тег
        article = soup.find('article')
        if article:
            paragraphs = article.find_all('p')
            if paragraphs:
                text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                text_parts = [p for p in text_parts if len(p) > 20]
                if text_parts:
                    return ' '.join(text_parts)
        
        # Способ 2: Ищем div с классом article-text, article-body, content и т.д.
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
        
        # Способ 3: Ищем все параграфы на странице
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
                filtered_parts = HTMLExtractor._filter_text_parts(text_parts)
                if filtered_parts:
                    main_text = [p for p in filtered_parts if len(p) > 100]
                    if main_text:
                        return ' '.join(main_text[:15])
                    else:
                        return ' '.join(filtered_parts[:10])
        
        return ""
    
    @staticmethod
    def _filter_text_parts(text_parts: list) -> list:
        """Фильтрация параграфов от рекламы и служебной информации"""
        skip_phrases = [
            'читайте рбк', 'реклама', 'подписка', 'cookie', 
            'политика конфиденциальности', 'какое вино подать',
            'как приготовить', 'чем занять детей', 'как легко завести разговор',
            'из каких сыров', 'что делать, если пролил', 'какие есть правила',
            'какие игры можно', 'как легко запомнить', 'попробуйте новую функцию',
            'гигачат', 'пао «сбербанк»', '18+'
        ]
        
        filtered_parts = []
        for p in text_parts:
            if len(p) < 50:
                continue
            if any(phrase in p.lower() for phrase in skip_phrases):
                continue
            if re.match(r'^(Фото|Видео|Фото:|Видео:)', p, re.I):
                continue
            filtered_parts.append(p)
        
        return filtered_parts

