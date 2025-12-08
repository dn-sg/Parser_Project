"""
Базовый класс для парсеров
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json
import time


class BaseParser:
    """Базовый класс для всех парсеров"""
    
    def __init__(self, url: str, headers: Optional[Dict] = None):
        """
        Инициализация парсера
        
        Args:
            url: URL страницы для парсинга
            headers: Заголовки HTTP запроса
        """
        self.url = url
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def fetch_html(self) -> Optional[str]:
        """
        Получение HTML содержимого страницы
        
        Returns:
            HTML содержимое или None в случае ошибки
        """
        try:
            response = self.session.get(self.url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Ошибка при получении HTML: {e}")
            return None
    
    def parse(self) -> List[Dict]:
        """
        Основной метод парсинга. Должен быть переопределен в дочерних классах
        
        Returns:
            Список словарей с данными о компаниях/акциях
        """
        raise NotImplementedError("Метод parse() должен быть реализован в дочернем классе")
    
    def to_json(self, data: List[Dict]) -> str:
        """
        Преобразование данных в JSON строку
        
        Args:
            data: Список словарей с данными
            
        Returns:
            JSON строка
        """
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def get_parsed_data(self) -> str:
        """
        Получение данных в формате JSON
        
        Returns:
            JSON строка с данными
        """
        data = self.parse()
        return self.to_json(data)

