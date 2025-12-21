"""
HTTP клиент для получения HTML страниц
"""
import requests
from typing import Optional, Dict
from abc import ABC, abstractmethod


class IHttpClient(ABC):
    """Интерфейс HTTP клиента"""
    
    @abstractmethod
    def get_html(self, url: str, headers: Optional[Dict] = None) -> Optional[str]:
        """Получение HTML содержимого страницы"""
        pass


class HttpClient(IHttpClient):
    """Реализация HTTP клиента"""
    
    def __init__(self, default_headers: Optional[Dict] = None):
        self.session = requests.Session()
        self.default_headers = default_headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session.headers.update(self.default_headers)
    
    def get_html(self, url: str, headers: Optional[Dict] = None) -> Optional[str]:
        """
        Получение HTML содержимого страницы
        
        Args:
            url: URL страницы
            headers: Дополнительные заголовки HTTP запроса
            
        Returns:
            HTML содержимое или None в случае ошибки
        """
        try:
            request_headers = {**self.default_headers}
            if headers:
                request_headers.update(headers)
            
            response = self.session.get(url, headers=request_headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Ошибка при получении HTML: {e}")
            return None

